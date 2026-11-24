"""Links budget entities to the institutions directory, and indexes them for search.

Usage:  python -m app.budget.links   (also run by `app.ingestion.cli all`)

The two sources share no identifier: MinHacienda's budget data uses the budget
code ("02-12-00") and no NIT; Función Pública's directory has neither. The rule
(assumption A-014, the same strictness the owner chose for bill authors, A-012):
a budget entity is linked to an institution only when their names, without case,
accents, punctuation or extra spaces, are equal and match exactly one institution.
Looser rules were measured on 2026-11-24 and rejected: dropping the " - GESTIÓN
GENERAL" kind of suffix also maps distinct bodies (the energy regulator CREG onto
the Ministry of Mines). Each link is an analytical association, labelled so, and
the derived data is rebuilt on every run.
"""

import uuid
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import ColumnElement, delete, select
from sqlalchemy.orm import Session

from app.budget.models import BudgetExecution
from app.catalog.models import Institution
from app.core.db import get_engine
from app.core.labels import ConfidenceClass, EpistemicLabel
from app.core.relationships import Relationship, public_only
from app.ingestion.text import normalize_name
from app.search.indexing import BUDGET_ENTITY, SearchEntry, index_entry
from app.search.models import SearchDocument

PREDICATE = "has_budget_line"
METHOD_NOTE = "nombre_exacto: coincidencia exacta y única con una entidad del directorio (A-014)"
LINK_RULE = (
    "Vínculo calculado por NEXO: el nombre de la entidad en el presupuesto coincide exactamente "
    "(sin contar mayúsculas, tildes ni signos) con el de una sola entidad del directorio de "
    "Función Pública. Las dos fuentes no comparten un código; es una asociación analítica, no un "
    "dato oficial. Muchas entidades del presupuesto no quedan enlazadas por esta regla estricta."
)


@dataclass(frozen=True)
class LinkedInstitution:
    institution_id: uuid.UUID
    name: str


@dataclass(frozen=True)
class LinkedBudgetEntity:
    entity_code: str
    entity_name: str


def _public_links() -> list[ColumnElement[bool]]:
    return [
        Relationship.subject_type == "institution",
        Relationship.predicate == PREDICATE,
        Relationship.object_type == "budget_execution",
        public_only(),
    ]


def institution_for_budget_entity(session: Session, entity_code: str) -> LinkedInstitution | None:
    row = session.execute(
        select(Institution.id, Institution.name)
        .join(Relationship, Relationship.subject_id == Institution.id)
        .join(BudgetExecution, BudgetExecution.id == Relationship.object_id)
        .where(BudgetExecution.entity_code == entity_code, *_public_links())
        .limit(1)
    ).first()
    return LinkedInstitution(institution_id=row[0], name=row[1]) if row else None


def budget_entity_for_institution(
    session: Session, institution_id: uuid.UUID
) -> LinkedBudgetEntity | None:
    row = session.execute(
        select(BudgetExecution.entity_code, BudgetExecution.entity_name)
        .join(Relationship, Relationship.object_id == BudgetExecution.id)
        .where(Relationship.subject_id == institution_id, *_public_links())
        .order_by(BudgetExecution.entity_code)
        .limit(1)
    ).first()
    return LinkedBudgetEntity(entity_code=row[0], entity_name=row[1]) if row else None


@dataclass(frozen=True)
class LinkResult:
    budget_entities: int
    linked: int


def link_budget_institutions(session: Session) -> LinkResult:
    session.execute(
        delete(Relationship).where(
            Relationship.predicate == PREDICATE, Relationship.method_note == METHOD_NOTE
        )
    )
    by_name: dict[str, list[uuid.UUID]] = defaultdict(list)
    for institution_id, name in session.execute(select(Institution.id, Institution.name)):
        by_name[normalize_name(name)].append(institution_id)

    lines: dict[str, list[BudgetExecution]] = defaultdict(list)
    for line in session.scalars(select(BudgetExecution)):
        lines[line.entity_code].append(line)

    linked = 0
    for entity_lines in lines.values():
        name = entity_lines[0].entity_name
        matches = by_name.get(normalize_name(name), [])
        if len(matches) != 1:
            continue
        linked += 1
        for line in entity_lines:
            session.add(
                Relationship(
                    subject_type="institution",
                    subject_id=matches[0],
                    predicate=PREDICATE,
                    object_type="budget_execution",
                    object_id=line.id,
                    confidence_class=ConfidenceClass.ANALYTICAL_ASSOCIATION.value,
                    epistemic_label=EpistemicLabel.HIPOTESIS_ANALITICA.value,
                    source_record_id=line.source_record_id,
                    method_note=METHOD_NOTE,
                    evidence=name,
                )
            )
    session.commit()
    return LinkResult(budget_entities=len(lines), linked=linked)


def index_budget_entities(session: Session) -> int:
    """One search document per budget entity, keyed by its first line's id."""
    session.execute(delete(SearchDocument).where(SearchDocument.record_type == BUDGET_ENTITY))
    lines: dict[str, list[BudgetExecution]] = defaultdict(list)
    for line in session.scalars(select(BudgetExecution).order_by(BudgetExecution.id)):
        lines[line.entity_code].append(line)
    for code, entity_lines in lines.items():
        first = entity_lines[0]
        index_entry(
            session,
            SearchEntry(
                record_type=BUDGET_ENTITY,
                record_id=first.id,
                title=first.entity_name,
                summary=" · ".join(
                    part for part in ("Ejecución presupuestal", first.sector_name, code) if part
                ),
                weighted_text={
                    "A": [first.entity_name, code],
                    "B": [first.sector_name],
                    "C": ["presupuesto ejecución apropiación"],
                },
            ),
        )
    return len(lines)


if __name__ == "__main__":
    with Session(get_engine()) as _session:
        result = link_budget_institutions(_session)
        indexed = index_budget_entities(_session)
        _session.commit()
        print(
            f"presupuesto: entidades={result.budget_entities} enlazadas={result.linked} "
            f"indexadas={indexed}"
        )
