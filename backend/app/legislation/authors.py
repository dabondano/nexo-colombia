"""Links bills to the representatives among their authors.

Usage:  python -m app.legislation.authors   (also run by `app.ingestion.cli all`)

Authors are published as free text, for example
"H.R. Ana Pérez Gómez, Juan Ruiz Díaz, y otras firmas". The rule, chosen by
the project owner on 2026-11-18, is deliberately strict:

1. The text is split at commas; courtesy titles (H.R., H.S., Hon.) and the
   closing "y otras firmas" are removed.
2. Each name is compared with the representatives of the period loaded, after
   removing case, accents, punctuation and extra spaces. A link is made only
   when the name matches exactly one representative.
3. Only bills filed on or after the start of that period's term
   (20 July 2026) are considered, because the list of representatives covers
   this term alone and an earlier namesake could be another person.

Names that do not match stay as published text. A link is NEXO's analytical
association, not a statement by the source, and pages say so.

The links are derived data: every run replaces them all.
"""

import re
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.congress.models import InitiativeAuthor, Person, PositionHolding
from app.core.db import get_engine
from app.ingestion.datasets.representatives import PERIOD
from app.ingestion.text import normalize_name
from app.legislation.models import LegislativeInitiative

AUTHOR_RULE = (
    "Vínculo calculado por NEXO: el nombre publicado entre los autores del proyecto "
    "coincide exactamente (sin contar mayúsculas, tildes ni signos) con el de un solo "
    "representante del período, y el proyecto se radicó desde el 20 de julio de 2026. "
    "La fuente no identifica a los autores; es una asociación analítica, no un dato oficial."
)
MATCH_METHOD = "nombre_exacto"
TERM_START = date(2026, 7, 20)

_TITLES = re.compile(r"^(?:(?:h\.?\s*[rs]\.?|hon\.?|honorable)\s+)+", re.IGNORECASE)
_OTHERS = re.compile(r"^(?:y\s+)?otr[oa]s(?:\s+firmas)?\.?$", re.IGNORECASE)


@dataclass(frozen=True)
class LinkResult:
    initiatives_considered: int
    authors_seen: int
    links: int
    ambiguous: int


def split_authors(text: str) -> list[str]:
    """The individual author names in a published list, in their published form."""
    names: list[str] = []
    for piece in text.split(","):
        name = " ".join(piece.split())
        name = re.sub(r"^y\s+", "", name, flags=re.IGNORECASE)
        name = _TITLES.sub("", name).strip()
        if name and not _OTHERS.fullmatch(name):
            names.append(name)
    return names


def link_authors(session: Session) -> LinkResult:
    session.execute(delete(InitiativeAuthor).where(InitiativeAuthor.match_method == MATCH_METHOD))

    people: dict[str, set[uuid.UUID]] = defaultdict(set)
    rows = session.execute(
        select(Person.id, Person.name_normalized)
        .join(PositionHolding, PositionHolding.person_id == Person.id)
        .where(PositionHolding.period == PERIOD)
    )
    for person_id, normalized in rows:
        people[normalized].add(person_id)

    initiatives = session.execute(
        select(LegislativeInitiative.id, LegislativeInitiative.authors_text).where(
            LegislativeInitiative.authors_text.is_not(None),
            or_(
                LegislativeInitiative.camara_filed_on >= TERM_START,
                LegislativeInitiative.senado_filed_on >= TERM_START,
            ),
        )
    ).all()

    considered = seen = links = ambiguous = 0
    for initiative_id, authors_text in initiatives:
        considered += 1
        linked: set[uuid.UUID] = set()
        for name in split_authors(authors_text or ""):
            seen += 1
            matches = people.get(normalize_name(name), set())
            if len(matches) > 1:
                ambiguous += 1
            if len(matches) != 1:
                continue
            (person_id,) = matches
            if person_id in linked:
                continue
            linked.add(person_id)
            session.add(
                InitiativeAuthor(
                    initiative_id=initiative_id,
                    person_id=person_id,
                    author_name=name,
                    match_method=MATCH_METHOD,
                )
            )
            links += 1
    session.commit()
    return LinkResult(considered, seen, links, ambiguous)


if __name__ == "__main__":
    with Session(get_engine()) as _session:
        result = link_authors(_session)
        print(
            f"autores: proyectos={result.initiatives_considered} "
            f"nombres={result.authors_seen} vínculos={result.links} "
            f"ambiguos={result.ambiguous}"
        )
