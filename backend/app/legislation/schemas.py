"""API schemas for legislative initiatives."""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.core.labels import EpistemicLabel
from app.core.listing import FilterOption
from app.core.provenance import ProvenanceOut


class InitiativeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    camara_number: str | None
    senado_number: str | None
    short_title: str | None
    title: str
    law_type: str | None
    status: str | None
    origin_chamber: str | None
    commission: str | None
    legislature: str | None
    camara_filed_on: date | None
    data_quality_status: str


class InitiativeOut(InitiativeSummary):
    senado_filed_on: date | None
    purpose: str | None
    observations: str | None
    # Authors exactly as the source publishes them; not linked to person records yet.
    authors_text: str | None
    jurisdiction_code: str
    # Registry data copied from an official database (brief section 2.1).
    epistemic_label: EpistemicLabel = EpistemicLabel.HECHO_DOCUMENTADO
    provenance: ProvenanceOut


class InitiativePage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[InitiativeSummary]


class InitiativeFilters(BaseModel):
    legislature: list[FilterOption]
    law_type: list[FilterOption]
    status: list[FilterOption]
    commission: list[FilterOption]
    origin_chamber: list[FilterOption]
