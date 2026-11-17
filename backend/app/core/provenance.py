"""Provenance shown with every public record (PRD FR-PLT-03).

A canonical record points at the raw item it was derived from
(`core.source_record`), which in turn points at its source in the registry.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.pipeline import REPAIR_STEP
from app.sources.models import Source, SourceRecord


class ProvenanceOut(BaseModel):
    source_id: uuid.UUID
    source_name: str
    source_institution: str
    # The dataset or site the record was taken from.
    source_url: str
    # The record's own page at the source, when the source provides one.
    original_url: str | None
    licence: str | None
    reliability_class: int
    source_verification_status: str
    extraction_method: str
    acquired_at: datetime
    published_at: datetime | None
    last_verified_at: datetime | None
    # Repairs NEXO made to the item as published, in plain Spanish. Empty for most records.
    processing_notes: list[str]


def load_provenance(session: Session, source_record_id: uuid.UUID) -> ProvenanceOut:
    record, source = session.execute(
        select(SourceRecord, Source)
        .join(Source, Source.id == SourceRecord.source_id)
        .where(SourceRecord.id == source_record_id)
    ).one()
    return ProvenanceOut(
        source_id=source.id,
        source_name=source.name,
        source_institution=source.institution,
        source_url=source.url,
        original_url=record.original_url,
        licence=source.licence,
        reliability_class=source.reliability_class,
        source_verification_status=source.verification_status,
        extraction_method=record.extraction_method,
        acquired_at=record.acquired_at,
        published_at=record.published_at,
        last_verified_at=record.last_verified_at,
        processing_notes=[
            str(step["note"])
            for step in record.processing_history
            if step.get("step") == REPAIR_STEP and step.get("note")
        ],
    )
