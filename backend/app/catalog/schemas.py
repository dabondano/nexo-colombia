"""API schemas for the institutions directory."""

import uuid

from pydantic import BaseModel, ConfigDict

from app.budget.links import LINK_RULE
from app.core.labels import EpistemicLabel
from app.core.listing import FilterOption
from app.core.provenance import ProvenanceOut


class InstitutionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    official_code: str
    name: str
    order: str | None
    suborder: str | None
    organic_classification: str | None
    sector: str | None
    legal_nature: str | None
    department: str | None
    municipality: str | None
    data_quality_status: str


class LinkedBudgetEntityOut(BaseModel):
    entity_code: str
    entity_name: str


class InstitutionOut(InstitutionSummary):
    nit: str | None
    level: str | None
    institution_type: str | None
    website: str | None
    longitude: float | None
    latitude: float | None
    status: str | None
    jurisdiction_code: str
    # An analytical association computed by NEXO (A-014), not part of the directory.
    budget_entity: LinkedBudgetEntityOut | None = None
    budget_entity_label: EpistemicLabel = EpistemicLabel.HIPOTESIS_ANALITICA
    budget_entity_rule: str = LINK_RULE
    # Contracts in NEXO's SECOP window linked to this entity by NIT (A-016).
    contract_count: int = 0
    # Directory data copied from an official database (brief section 2.1).
    epistemic_label: EpistemicLabel = EpistemicLabel.HECHO_DOCUMENTADO
    provenance: ProvenanceOut


class InstitutionPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[InstitutionSummary]


class InstitutionFilters(BaseModel):
    order: list[FilterOption]
    organic_classification: list[FilterOption]
    sector: list[FilterOption]
    department: list[FilterOption]
