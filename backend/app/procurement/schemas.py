"""API schemas for public contracts (SECOP II)."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.core.labels import EpistemicLabel
from app.core.listing import FilterOption
from app.core.provenance import ProvenanceOut

SUPPLIER_LABELS = {
    "empresa": "Empresa u otra persona jurídica",
    "persona_natural": "Persona natural",
    "sin_definir": "Sin definir en la fuente",
}
PRIVACY_NOTE = (
    "NEXO no muestra el nombre ni el documento de los contratistas que son personas naturales, ni "
    "los datos de funcionarios, supervisores o cuentas bancarias que también publica SECOP. Los "
    "datos completos pueden consultarse en SECOP con el enlace del proceso."
)
WINDOW_NOTE = (
    "NEXO conserva los contratos de entidades del orden nacional firmados en los últimos {days} "
    "días (desde el {start}). Los anteriores siguen disponibles en SECOP II."
)
VALUE_NOTE = (
    "Valores en pesos, tal como los publica la entidad en SECOP II. La entidad es responsable de "
    "su exactitud; un valor de 0 puede corresponder, por ejemplo, a un comodato o a un convenio "
    "sin recursos."
)


class LinkedInstitutionOut(BaseModel):
    institution_id: uuid.UUID
    name: str


class ContractSummary(BaseModel):
    id: uuid.UUID
    source_key: str
    purpose: str
    entity_name: str
    supplier_name: str | None
    supplier_kind: str
    supplier_label: str
    contract_type: str | None
    modality: str | None
    status: str | None
    signed_on: date
    value: Decimal


class ContractPage(BaseModel):
    total: int
    limit: int
    offset: int
    window_note: str
    items: list[ContractSummary]


class ContractFilters(BaseModel):
    contract_type: list[FilterOption]
    modality: list[FilterOption]
    status: list[FilterOption]


class ContractOut(ContractSummary):
    process_id: str | None
    reference: str | None
    entity_nit: str | None
    institution: LinkedInstitutionOut | None
    institution_rule: str
    department: str | None
    city: str | None
    sector: str | None
    branch: str | None
    modality_reason: str | None
    start_on: date | None
    end_on: date | None
    duration_text: str | None
    days_added: int | None
    supplier_nit: str | None
    supplier_is_sme: bool | None
    resource_origin: str | None
    spending_type: str | None
    invoiced: Decimal | None
    paid: Decimal | None
    pending_payment: Decimal | None
    pending_execution: Decimal | None
    process_url: str | None
    source_updated_at: datetime | None
    data_quality_status: str
    jurisdiction_code: str
    privacy_note: str = PRIVACY_NOTE
    value_note: str = VALUE_NOTE
    window_note: str
    # Copied from an official database (brief section 2.1).
    epistemic_label: EpistemicLabel = EpistemicLabel.HECHO_DOCUMENTADO
    provenance: ProvenanceOut
