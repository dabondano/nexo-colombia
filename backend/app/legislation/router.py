"""Public, read-only endpoints for legislative initiatives ("Legislación")."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

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
from app.legislation.models import LegislativeInitiative
from app.legislation.schemas import (
    InitiativeFilters,
    InitiativeOut,
    InitiativePage,
    InitiativeSummary,
)

router = APIRouter(prefix="/initiatives", tags=["initiatives"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=InitiativePage)
def list_initiatives(
    session: SessionDep,
    q: SearchParam = None,
    author: SearchParam = None,
    legislature: FilterParam = None,
    law_type: FilterParam = None,
    status: FilterParam = None,
    commission: FilterParam = None,
    origin_chamber: FilterParam = None,
    limit: LimitParam = DEFAULT_LIMIT,
    offset: OffsetParam = 0,
) -> InitiativePage:
    initiative = LegislativeInitiative
    statement = select(initiative)
    if q:
        statement = statement.where(*contains_all_words(initiative.title_normalized, q))
    if author:
        statement = statement.where(*contains_all_words(initiative.authors_normalized, author))
    if legislature:
        statement = statement.where(initiative.legislature == legislature)
    if law_type:
        statement = statement.where(initiative.law_type == law_type)
    if status:
        statement = statement.where(initiative.status == status)
    if commission:
        statement = statement.where(initiative.commission == commission)
    if origin_chamber:
        statement = statement.where(initiative.origin_chamber == origin_chamber)

    total = count_rows(session, statement)
    # Newest legislature first, then filing date; undated records go last.
    rows = session.scalars(
        statement.order_by(
            initiative.legislature.desc().nulls_last(),
            initiative.camara_filed_on.desc().nulls_last(),
            initiative.source_key,
        )
        .limit(limit)
        .offset(offset)
    ).all()
    return InitiativePage(
        total=total,
        limit=limit,
        offset=offset,
        items=[InitiativeSummary.model_validate(row) for row in rows],
    )


@router.get("/filters", response_model=InitiativeFilters)
def initiative_filters(session: SessionDep) -> InitiativeFilters:
    initiative = LegislativeInitiative
    return InitiativeFilters(
        legislature=sorted(
            filter_options(session, initiative.legislature), key=lambda o: o.value, reverse=True
        ),
        law_type=filter_options(session, initiative.law_type),
        status=filter_options(session, initiative.status),
        commission=filter_options(session, initiative.commission),
        origin_chamber=filter_options(session, initiative.origin_chamber),
    )


@router.get("/{initiative_id}", response_model=InitiativeOut)
def get_initiative(initiative_id: uuid.UUID, session: SessionDep) -> InitiativeOut:
    initiative = session.get(LegislativeInitiative, initiative_id)
    if initiative is None:
        raise HTTPException(status_code=404, detail="Iniciativa no encontrada")
    summary = InitiativeSummary.model_validate(initiative).model_dump()
    return InitiativeOut(
        **summary,
        senado_filed_on=initiative.senado_filed_on,
        purpose=initiative.purpose,
        observations=initiative.observations,
        authors_text=initiative.authors_text,
        jurisdiction_code=initiative.jurisdiction_code,
        provenance=load_provenance(session, initiative.source_record_id),
    )
