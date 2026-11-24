"""Public, read-only endpoints for the representatives directory ("Congreso")."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.congress.models import Person, PositionHolding
from app.congress.schemas import (
    AuthoredInitiative,
    RepresentativeFilters,
    RepresentativeOut,
    RepresentativePage,
    RepresentativeSummary,
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
from app.core.relationships import Relationship, public_only
from app.legislation.authors import AUTHOR_RULE
from app.legislation.authors import PREDICATE as AUTHOR_PREDICATE
from app.legislation.models import LegislativeInitiative

router = APIRouter(prefix="/representatives", tags=["congress"])

SessionDep = Annotated[Session, Depends(get_session)]


def _summary(holding: PositionHolding, person: Person) -> RepresentativeSummary:
    return RepresentativeSummary(
        id=holding.id,
        person_id=person.id,
        full_name=person.full_name,
        position=holding.position,
        corporation=holding.corporation,
        period=holding.period,
        constituency=holding.constituency,
        party=holding.party,
        seat_basis=holding.seat_basis,
        data_quality_status=holding.data_quality_status,
    )


def _base() -> Select[PositionHolding, Person]:
    return select(PositionHolding, Person).join(Person, Person.id == PositionHolding.person_id)


@router.get("", response_model=RepresentativePage)
def list_representatives(
    session: SessionDep,
    q: SearchParam = None,
    constituency: FilterParam = None,
    party: FilterParam = None,
    limit: LimitParam = DEFAULT_LIMIT,
    offset: OffsetParam = 0,
) -> RepresentativePage:
    statement = _base()
    if q:
        statement = statement.where(*contains_all_words(Person.name_normalized, q))
    if constituency:
        statement = statement.where(PositionHolding.constituency == constituency)
    if party:
        statement = statement.where(PositionHolding.party == party)
    total = count_rows(session, statement)
    # Alphabetical order: a neutral ordering that ranks no person above another.
    rows = session.execute(
        statement.order_by(Person.name_normalized, PositionHolding.id).limit(limit).offset(offset)
    ).all()
    return RepresentativePage(
        total=total,
        limit=limit,
        offset=offset,
        items=[_summary(holding, person) for holding, person in rows],
    )


@router.get("/filters", response_model=RepresentativeFilters)
def representative_filters(session: SessionDep) -> RepresentativeFilters:
    return RepresentativeFilters(
        constituency=filter_options(session, PositionHolding.constituency),
        party=filter_options(session, PositionHolding.party),
    )


@router.head("/{representative_id}", include_in_schema=False)
def representative_exists(representative_id: uuid.UUID, session: SessionDep) -> Response:
    """Existence check without the record body, used by the web app to answer 404 early."""
    found = session.scalar(
        select(PositionHolding.id).where(PositionHolding.id == representative_id)
    )
    return Response(status_code=200 if found else 404)


@router.get("/{representative_id}", response_model=RepresentativeOut)
def get_representative(representative_id: uuid.UUID, session: SessionDep) -> RepresentativeOut:
    row = session.execute(_base().where(PositionHolding.id == representative_id)).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Representante no encontrado")
    holding, person = row
    authored = session.execute(
        select(LegislativeInitiative, Relationship.evidence)
        .join(Relationship, Relationship.object_id == LegislativeInitiative.id)
        .where(
            Relationship.subject_type == "person",
            Relationship.subject_id == person.id,
            Relationship.predicate == AUTHOR_PREDICATE,
            Relationship.object_type == "legislative_initiative",
            public_only(),
        )
        .order_by(
            LegislativeInitiative.camara_filed_on.desc().nulls_last(),
            LegislativeInitiative.title_normalized,
        )
    ).all()
    return RepresentativeOut(
        **_summary(holding, person).model_dump(),
        email=holding.email,
        office=holding.office,
        phone=holding.phone,
        jurisdiction_code=holding.jurisdiction_code,
        provenance=load_provenance(session, holding.source_record_id),
        authored_initiatives=[
            AuthoredInitiative(
                id=initiative.id,
                title=initiative.short_title or initiative.title,
                camara_number=initiative.camara_number,
                senado_number=initiative.senado_number,
                legislature=initiative.legislature,
                status=initiative.status,
                author_name=author_name or "",
            )
            for initiative, author_name in authored
        ],
        authored_initiatives_rule=AUTHOR_RULE,
    )
