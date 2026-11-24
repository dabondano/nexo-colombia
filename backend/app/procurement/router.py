"""Public, read-only endpoints for SECOP II contracts ("Contratos").

Lists are ordered by signing date, newest first, then by SECOP identifier: a
neutral order that ranks no entity or contractor above another. There is no
ordering by value.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.catalog.models import Institution
from app.core.config import get_settings
from app.core.db import get_session
from app.core.listing import (
    DEFAULT_LIMIT,
    FilterParam,
    LimitParam,
    OffsetParam,
    SearchParam,
    contains_all_words,
    count_rows,
    filter_options,
)
from app.core.provenance import load_provenance
from app.ingestion.datasets.contracts import window_start
from app.procurement.links import LINK_RULE
from app.procurement.models import Contract
from app.procurement.schemas import (
    SUPPLIER_LABELS,
    WINDOW_NOTE,
    ContractFilters,
    ContractOut,
    ContractPage,
    ContractSummary,
    LinkedInstitutionOut,
)

router = APIRouter(prefix="/contracts", tags=["contracts"])
SessionDep = Annotated[Session, Depends(get_session)]


def window_note() -> str:
    return WINDOW_NOTE.format(
        days=get_settings().secop_window_days, start=window_start().strftime("%d/%m/%Y")
    )


def _summary(contract: Contract) -> ContractSummary:
    return ContractSummary(
        id=contract.id,
        source_key=contract.source_key,
        purpose=contract.purpose,
        entity_name=contract.entity_name,
        supplier_name=contract.supplier_name,
        supplier_kind=contract.supplier_kind,
        supplier_label=SUPPLIER_LABELS.get(contract.supplier_kind, contract.supplier_kind),
        contract_type=contract.contract_type,
        modality=contract.modality,
        status=contract.status,
        signed_on=contract.signed_on,
        value=contract.value,
    )


@router.get("", response_model=ContractPage)
def list_contracts(
    session: SessionDep,
    q: SearchParam = None,
    institution: Annotated[uuid.UUID | None, Query(description="Entidad del directorio")] = None,
    contract_type: FilterParam = None,
    modality: FilterParam = None,
    status: FilterParam = None,
    limit: LimitParam = DEFAULT_LIMIT,
    offset: OffsetParam = 0,
) -> ContractPage:
    statement = select(Contract)
    if q:
        # Words of the contract's purpose; the entity is chosen with `institution`.
        statement = statement.where(*contains_all_words(Contract.purpose_normalized, q))
    if institution:
        statement = statement.where(Contract.institution_id == institution)
    if contract_type:
        statement = statement.where(Contract.contract_type == contract_type)
    if modality:
        statement = statement.where(Contract.modality == modality)
    if status:
        statement = statement.where(Contract.status == status)
    total = count_rows(session, statement)
    rows = session.scalars(
        statement.order_by(Contract.signed_on.desc(), Contract.source_key)
        .limit(limit)
        .offset(offset)
    ).all()
    return ContractPage(
        total=total,
        limit=limit,
        offset=offset,
        window_note=window_note(),
        items=[_summary(row) for row in rows],
    )


@router.get("/filters", response_model=ContractFilters)
def contract_filters(session: SessionDep) -> ContractFilters:
    return ContractFilters(
        contract_type=filter_options(session, Contract.contract_type),
        modality=filter_options(session, Contract.modality),
        status=filter_options(session, Contract.status),
    )


@router.head("/{contract_id}", include_in_schema=False)
def contract_exists(contract_id: uuid.UUID, session: SessionDep) -> Response:
    """Existence check without the record body, used by the web app to answer 404 early."""
    found = session.scalar(select(Contract.id).where(Contract.id == contract_id))
    return Response(status_code=200 if found else 404)


@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(contract_id: uuid.UUID, session: SessionDep) -> ContractOut:
    contract = session.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    institution = (
        session.get(Institution, contract.institution_id) if contract.institution_id else None
    )
    return ContractOut(
        **_summary(contract).model_dump(),
        process_id=contract.process_id,
        reference=contract.reference,
        entity_nit=contract.entity_nit,
        institution=(
            LinkedInstitutionOut(institution_id=institution.id, name=institution.name)
            if institution
            else None
        ),
        institution_rule=LINK_RULE,
        department=contract.department,
        city=contract.city,
        sector=contract.sector,
        branch=contract.branch,
        modality_reason=contract.modality_reason,
        start_on=contract.start_on,
        end_on=contract.end_on,
        duration_text=contract.duration_text,
        days_added=contract.days_added,
        supplier_nit=contract.supplier_nit,
        supplier_is_sme=contract.supplier_is_sme,
        resource_origin=contract.resource_origin,
        spending_type=contract.spending_type,
        invoiced=contract.invoiced,
        paid=contract.paid,
        pending_payment=contract.pending_payment,
        pending_execution=contract.pending_execution,
        process_url=contract.process_url,
        source_updated_at=contract.source_updated_at,
        data_quality_status=contract.data_quality_status,
        jurisdiction_code=contract.jurisdiction_code,
        window_note=window_note(),
        provenance=load_provenance(session, contract.source_record_id),
    )
