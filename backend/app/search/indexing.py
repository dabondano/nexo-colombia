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
from app.congress.models import Person, PositionHolding
from app.ingestion.text import normalize_for_search
from app.law.models import LegalInstrument, LegalProvision
from app.legislation.models import LegislativeInitiative
from app.procurement.models import Contract
from app.search.models import SearchDocument

TEXT_CONFIG = "spanish"
# PostgreSQL's four text-search weights, as SQL literals.
WEIGHTS: dict[str, ColumnElement[Any]] = {w: literal_column(f"'{w}'") for w in "ABCD"}

INSTITUTION = "institution"
LEGISLATIVE_INITIATIVE = "legislative_initiative"
LEGAL_PROVISION = "legal_provision"
REPRESENTATIVE = "representative"
BUDGET_ENTITY = "budget_entity"
CONTRACT = "contract"
RECORD_TYPES = (
    LEGAL_PROVISION,
    LEGISLATIVE_INITIATIVE,
    REPRESENTATIVE,
    INSTITUTION,
    BUDGET_ENTITY,
    CONTRACT,
)
SUPPLIER_KINDS = {"persona_natural": "Persona natural", "sin_definir": "Contratista sin definir"}
SUMMARY_LENGTH = 240


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
        "title_tsv": func.to_tsvector(TEXT_CONFIG, normalize_for_search(entry.title)),
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


def contract_entry(contract: Contract) -> SearchEntry:
    supplier = contract.supplier_name or SUPPLIER_KINDS.get(contract.supplier_kind)
    return SearchEntry(
        record_type=CONTRACT,
        record_id=contract.id,
        title=_shorten(contract.purpose, 200),
        summary=_join([contract.entity_name, supplier, contract.contract_type]),
        record_date=contract.signed_on,
        weighted_text={
            "A": [contract.source_key, contract.reference, contract.process_id],
            "B": [contract.purpose, contract.entity_name, contract.supplier_name],
            "C": [contract.contract_type, contract.modality, contract.sector],
        },
    )


def _shorten(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


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


def representative_entry(holding: PositionHolding, person: Person) -> SearchEntry:
    return SearchEntry(
        record_type=REPRESENTATIVE,
        record_id=holding.id,
        title=person.full_name,
        summary=_join([holding.position, holding.constituency, holding.party, holding.period]),
        weighted_text={
            "A": [person.full_name],
            "B": [holding.constituency, holding.party, holding.position],
            "C": [holding.corporation, holding.period],
        },
    )


def excerpt(text: str, length: int = SUMMARY_LENGTH) -> str:
    """The beginning of a text, cut at a word and marked when it was cut."""
    flat = " ".join(text.split())
    if len(flat) <= length:
        return flat
    return flat[:length].rsplit(" ", 1)[0] + "…"


def provision_entry(
    provision: LegalProvision, instrument: LegalInstrument, text: str
) -> SearchEntry:
    """`text` is the wording the source presents as in force (no editor's notes)."""
    number = provision.number or ""
    return SearchEntry(
        record_type=LEGAL_PROVISION,
        record_id=provision.id,
        # Search results name the instrument with the record type.
        title=provision.label,
        summary=excerpt(text),
        weighted_text={
            # "articulo 11", "art 11" and the bare number all find the article.
            "A": [provision.label, f"art {number}" if number else None, provision.heading],
            "B": [instrument.title],
            "C": [text],
        },
    )
