"""API schemas for the representatives directory."""

import uuid

from pydantic import BaseModel

from app.core.labels import EpistemicLabel
from app.core.listing import FilterOption
from app.core.provenance import ProvenanceOut


class RepresentativeSummary(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    full_name: str
    position: str
    corporation: str
    period: str
    constituency: str | None
    party: str | None
    seat_basis: str | None
    data_quality_status: str


class AuthoredInitiative(BaseModel):
    id: uuid.UUID
    title: str
    camara_number: str | None
    senado_number: str | None
    legislature: str | None
    status: str | None
    # The name as it appears in the bill's list of authors.
    author_name: str


class RepresentativeOut(RepresentativeSummary):
    email: str | None
    office: str | None
    phone: str | None
    jurisdiction_code: str
    # Directory data copied from an official database (brief section 2.1).
    epistemic_label: EpistemicLabel = EpistemicLabel.HECHO_DOCUMENTADO
    provenance: ProvenanceOut
    # Bills linked to this person by NEXO's matching rule (an analytical association).
    authored_initiatives: list[AuthoredInitiative]
    authored_initiatives_label: EpistemicLabel = EpistemicLabel.HIPOTESIS_ANALITICA
    authored_initiatives_rule: str


class RepresentativePage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[RepresentativeSummary]


class RepresentativeFilters(BaseModel):
    constituency: list[FilterOption]
    party: list[FilterOption]


class LinkedAuthor(BaseModel):
    representative_id: uuid.UUID
    full_name: str
    author_name: str
