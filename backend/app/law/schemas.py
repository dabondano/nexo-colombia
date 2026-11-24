"""Response shapes for legal instruments and their provisions."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.core.provenance import ProvenanceOut


class InstrumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    title: str
    instrument_type: str
    number: str | None = None
    year: int | None
    promulgated_on: date | None = None
    official_publication_ref: str | None = None
    # What is known about how current the loaded edition is.
    edition_note: str | None


class OutlineItem(BaseModel):
    id: uuid.UUID
    parent_id: uuid.UUID | None
    path: str
    kind: str
    label: str
    heading: str | None
    # Beginning of the wording, for articles.
    excerpt: str | None
    data_quality_status: str


class InstrumentOut(InstrumentSummary):
    article_count: int
    # Articles whose wording the source mixes with earlier or struck-through text.
    articles_needing_review: int
    outline: list[OutlineItem]
    provenance: ProvenanceOut


class ProvisionRef(BaseModel):
    id: uuid.UUID
    path: str
    label: str
    heading: str | None


class SegmentOut(BaseModel):
    # "text": wording; "note": editor's note; "after_previous_mark": wording the
    # source prints after its mark "TEXTO ANTERIOR", which may not be in force.
    kind: str
    text: str


class ProvisionOut(BaseModel):
    id: uuid.UUID
    path: str
    kind: str
    label: str
    heading: str | None
    data_quality_status: str
    instrument: InstrumentSummary
    # Divisions that contain the provision, outermost first.
    ancestors: list[ProvisionRef]
    segments: list[SegmentOut]
    # When NEXO recorded this wording. It is not a legal date.
    recorded_at: datetime | None
    # Identifies the current wording; legal reviews are pinned to it.
    version_id: uuid.UUID | None
    previous: ProvisionRef | None
    next: ProvisionRef | None
    provenance: ProvenanceOut
