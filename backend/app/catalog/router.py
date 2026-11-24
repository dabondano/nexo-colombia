"""Public, read-only endpoints for the institutions directory ("Instituciones")."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.budget.links import budget_entity_for_institution
from app.catalog.models import Institution
from app.catalog.schemas import (
    InstitutionFilters,
    InstitutionOut,
    InstitutionPage,
    InstitutionSummary,
    LinkedBudgetEntityOut,
)
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
from app.procurement.models import Contract

router = APIRouter(prefix="/institutions", tags=["institutions"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=InstitutionPage)
def list_institutions(
    session: SessionDep,
    q: SearchParam = None,
    order: FilterParam = None,
    organic_classification: FilterParam = None,
    sector: FilterParam = None,
    department: FilterParam = None,
    limit: LimitParam = DEFAULT_LIMIT,
    offset: OffsetParam = 0,
) -> InstitutionPage:
    statement = select(Institution)
    if q:
        statement = statement.where(*contains_all_words(Institution.name_normalized, q))
    if order:
        statement = statement.where(Institution.order == order)
    if organic_classification:
        statement = statement.where(Institution.organic_classification == organic_classification)
    if sector:
        statement = statement.where(Institution.sector == sector)
    if department:
        statement = statement.where(Institution.department == department)

    total = count_rows(session, statement)
    # Alphabetical order: a neutral ordering that ranks no entity above another.
    rows = session.scalars(
        statement.order_by(Institution.name_normalized, Institution.official_code)
        .limit(limit)
        .offset(offset)
    ).all()
    return InstitutionPage(
        total=total,
        limit=limit,
        offset=offset,
        items=[InstitutionSummary.model_validate(row) for row in rows],
    )


@router.get("/filters", response_model=InstitutionFilters)
def institution_filters(session: SessionDep) -> InstitutionFilters:
    return InstitutionFilters(
        order=filter_options(session, Institution.order),
        organic_classification=filter_options(session, Institution.organic_classification),
        sector=filter_options(session, Institution.sector),
        department=filter_options(session, Institution.department),
    )


@router.head("/{institution_id}", include_in_schema=False)
def institution_exists(institution_id: uuid.UUID, session: SessionDep) -> Response:
    """Existence check without the record body, used by the web app to answer 404 early."""
    found = session.scalar(select(Institution.id).where(Institution.id == institution_id))
    return Response(status_code=200 if found else 404)


@router.get("/{institution_id}", response_model=InstitutionOut)
def get_institution(institution_id: uuid.UUID, session: SessionDep) -> InstitutionOut:
    institution = session.get(Institution, institution_id)
    if institution is None:
        raise HTTPException(status_code=404, detail="Entidad no encontrada")
    summary = InstitutionSummary.model_validate(institution).model_dump()
    return InstitutionOut(
        **summary,
        nit=institution.nit,
        level=institution.level,
        institution_type=institution.institution_type,
        website=institution.website,
        longitude=institution.longitude,
        latitude=institution.latitude,
        status=institution.status,
        jurisdiction_code=institution.jurisdiction_code,
        budget_entity=(
            LinkedBudgetEntityOut(entity_code=linked.entity_code, entity_name=linked.entity_name)
            if (linked := budget_entity_for_institution(session, institution.id))
            else None
        ),
        contract_count=session.scalar(
            select(func.count()).where(Contract.institution_id == institution.id)
        )
        or 0,
        provenance=load_provenance(session, institution.source_record_id),
    )
