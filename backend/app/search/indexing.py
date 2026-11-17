"""Builds and stores search documents for canonical records.

Text is indexed with PostgreSQL's Spanish configuration after removing accents
and capitals, and searches are prepared the same way (app/search/router.py).
A search for "educacion" therefore finds "EDUCACIÓN", and plurals match their
singular. Related words ("educativo") and synonyms are not matched.
"""

import re
import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from sqlalchemy import ColumnElement, func, literal_column
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.catalog.models import Institution
from app.ingestion.text import normalize_for_search
from app.legislation.models import LegislativeInitiative
from app.search.models import SearchDocument

TEXT_CONFIG = "spanish"
# PostgreSQL's four text-search weights, as SQL literals.
WEIGHTS: dict[str, ColumnElement[Any]] = {w: literal_column(f"'{w}'") for w in "ABCD"}

INSTITUTION = "institution"
LEGISLATIVE_INITIATIVE = "legislative_initiative"
RECORD_TYPES = (LEGISLATIVE_INITIATIVE, INSTITUTION)


@dataclass(frozen=True)
class SearchEntry:
    record_type: str
    record_id: uuid.UUID
    title: str
    summary: str | None
    record_date: date | None = None
    # Text by importance, from A (names, identifiers) to D (supporting text).
    # Importance only orders results by how well they match the words searched.
    weighted_text: dict[str, list[str | None]] = field(default_factory=dict)


def _vector(entry: SearchEntry) -> ColumnElement[Any]:
    vector: ColumnElement[Any] | None = None
    for weight, parts in sorted(entry.weighted_text.items()):
        text = " ".join(part for part in parts if part)
        if not text:
            continue
        piece = func.setweight(
            func.to_tsvector(TEXT_CONFIG, normalize_for_search(text)), WEIGHTS[weight]
        )
        vector = piece if vector is None else vector.op("||")(piece)
    return vector if vector is not None else func.to_tsvector(TEXT_CONFIG, "")


def index_entry(session: Session, entry: SearchEntry) -> None:
    """Insert or replace the search document of one record."""
    values = {
        "record_type": entry.record_type,
        "record_id": entry.record_id,
        "title": entry.title,
        "summary": entry.summary,
        "record_date": entry.record_date,
        "tsv": _vector(entry),
    }
    statement = insert(SearchDocument).values(id=uuid.uuid4(), **values)
    session.execute(
        statement.on_conflict_do_update(
            index_elements=[SearchDocument.record_type, SearchDocument.record_id],
            set_={**values, "updated_at": func.now()},
        )
    )


def _join(parts: list[str | None], separator: str = " · ") -> str | None:
    present = [part for part in parts if part]
    return separator.join(present) if present else None


def number_variants(number: str | None) -> list[str]:
    """Ways people write a bill number: "217/2026C", "217/2026", "217 2026"."""
    if not number:
        return []
    compact = number.replace(" ", "")
    without_letter = re.sub(r"[A-Za-z]+$", "", compact)
    pieces = " ".join(re.findall(r"\d+", compact))
    return list(dict.fromkeys([number, compact, without_letter, pieces]))


def institution_entry(institution: Institution) -> SearchEntry:
    place = _join([institution.municipality, institution.department], ", ")
    return SearchEntry(
        record_type=INSTITUTION,
        record_id=institution.id,
        title=institution.name,
        summary=_join([institution.legal_nature, institution.order, place]),
        weighted_text={
            "A": [institution.name, institution.nit],
            "B": [institution.legal_nature, institution.sector, place],
            "C": [institution.order, institution.suborder, institution.organic_classification],
        },
    )


def initiative_entry(initiative: LegislativeInitiative) -> SearchEntry:
    numbers = _join(
        [
            f"Cámara {initiative.camara_number}" if initiative.camara_number else None,
            f"Senado {initiative.senado_number}" if initiative.senado_number else None,
        ]
    )
    legislature = f"Legislatura {initiative.legislature}" if initiative.legislature else None
    return SearchEntry(
        record_type=LEGISLATIVE_INITIATIVE,
        record_id=initiative.id,
        title=initiative.short_title or initiative.title,
        summary=_join(
            [
                initiative.title if initiative.short_title else None,
                numbers,
                initiative.law_type,
                legislature,
            ]
        ),
        record_date=initiative.camara_filed_on or initiative.senado_filed_on,
        weighted_text={
            "A": [
                initiative.short_title,
                initiative.title,
                *number_variants(initiative.camara_number),
                *number_variants(initiative.senado_number),
            ],
            "B": [initiative.law_type, initiative.commission, initiative.legislature],
            "C": [initiative.purpose, initiative.status],
            "D": [initiative.authors_text],
        },
    )
