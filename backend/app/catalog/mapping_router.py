"""Staff endpoints for reviewed entity links (A-017). Data stewards and administrators."""

import uuid
from collections import defaultdict
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.deps import SessionDep, require_roles
from app.auth.models import Role, UserAccount
from app.budget.links import PREDICATE, link_budget_institutions
from app.budget.models import BudgetExecution
from app.catalog.mappings import EntityMapping, MappingKind, contract_key
from app.catalog.models import Institution
from app.core import audit
from app.core.listing import LimitParam, OffsetParam
from app.core.relationships import Relationship
from app.ingestion.text import normalize_for_search, normalize_name
from app.procurement.links import link_contract_institutions, nit_key
from app.procurement.models import Contract

router = APIRouter(prefix="/admin/entity-mappings", tags=["staff"])
StewardUser = Annotated[UserAccount, Depends(require_roles(Role.DATA_STEWARD))]
KindParam = Literal["budget_entity", "contract_entity"]


class Candidate(BaseModel):
    kind: str
    source_value: str
    source_name: str
    detail: str | None
    records: int
    reason: str


class CandidatePage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[Candidate]


class MappingIn(BaseModel):
    kind: KindParam
    source_value: str = Field(min_length=1, max_length=400)
    institution_id: uuid.UUID
    note: str = Field(min_length=10, max_length=1000)


class MappingOut(BaseModel):
    id: uuid.UUID
    kind: str
    source_value: str
    source_name: str
    institution_id: uuid.UUID
    institution_name: str
    note: str
    created_by_email: str | None
    created_at: datetime


def _budget_candidates(session: Session) -> list[Candidate]:
    linked = set(
        session.scalars(
            select(BudgetExecution.entity_code)
            .join(Relationship, Relationship.object_id == BudgetExecution.id)
            .where(Relationship.predicate == PREDICATE)
            .distinct()
        )
    )
    names: dict[str, int] = defaultdict(int)
    for (name,) in session.execute(select(Institution.name)):
        names[normalize_name(name)] += 1
    rows = session.execute(
        select(BudgetExecution.entity_code, BudgetExecution.entity_name, func.count())
        .group_by(BudgetExecution.entity_code, BudgetExecution.entity_name)
        .order_by(BudgetExecution.entity_name)
    )
    result = []
    for code, name, count in rows:
        if code in linked:
            continue
        same = names.get(normalize_name(name), 0)
        reason = (
            f"Hay {same} entidades del directorio con este mismo nombre."
            if same > 1
            else "Ninguna entidad del directorio tiene exactamente este nombre."
        )
        result.append(
            Candidate(
                kind=MappingKind.BUDGET_ENTITY.value,
                source_value=code,
                source_name=name,
                detail=f"Código {code}",
                records=count,
                reason=reason,
            )
        )
    return result


def _contract_candidates(session: Session) -> list[Candidate]:
    by_nit: dict[str, int] = defaultdict(int)
    for (nit,) in session.execute(select(Institution.nit).where(Institution.nit.is_not(None))):
        key = nit_key(nit)
        if key:
            by_nit[key] += 1
    rows = session.execute(
        select(Contract.entity_nit, Contract.entity_name, func.count())
        .where(Contract.institution_id.is_(None))
        .group_by(Contract.entity_nit, Contract.entity_name)
        # For the team's work list only: entities with more contracts first.
        .order_by(func.count().desc(), Contract.entity_name)
    )
    result = []
    for nit, name, count in rows:
        key = nit_key(nit)
        shared = by_nit.get(key, 0) if key else 0
        reason = (
            f"El NIT es de {shared} entidades del directorio."
            if shared > 1
            else "El NIT no aparece en el directorio."
        )
        result.append(
            Candidate(
                kind=MappingKind.CONTRACT_ENTITY.value,
                source_value=contract_key(nit, name),
                source_name=name,
                detail=f"NIT {nit}" if nit else "Sin NIT",
                records=count,
                reason=reason,
            )
        )
    return result


@router.get("/candidates", response_model=CandidatePage)
def candidates(
    session: SessionDep,
    _steward: StewardUser,
    kind: Annotated[KindParam, Query()],
    q: Annotated[str | None, Query(max_length=200)] = None,
    limit: LimitParam = 25,
    offset: OffsetParam = 0,
) -> CandidatePage:
    items = (
        _budget_candidates(session)
        if kind == MappingKind.BUDGET_ENTITY.value
        else _contract_candidates(session)
    )
    if q:
        words = normalize_for_search(q).split()
        items = [
            item
            for item in items
            if all(word in normalize_for_search(item.source_name) for word in words)
        ]
    return CandidatePage(
        total=len(items), limit=limit, offset=offset, items=items[offset : offset + limit]
    )


def _out(session: Session, mapping: EntityMapping) -> MappingOut:
    institution = session.get(Institution, mapping.institution_id)
    creator = session.get(UserAccount, mapping.created_by) if mapping.created_by else None
    return MappingOut(
        id=mapping.id,
        kind=mapping.kind,
        source_value=mapping.source_value,
        source_name=mapping.source_name,
        institution_id=mapping.institution_id,
        institution_name=institution.name if institution else "",
        note=mapping.note,
        created_by_email=creator.email if creator else None,
        created_at=mapping.created_at,
    )


@router.get("", response_model=list[MappingOut])
def list_mappings(session: SessionDep, _steward: StewardUser) -> list[MappingOut]:
    mappings = session.scalars(
        select(EntityMapping).order_by(EntityMapping.kind, EntityMapping.source_name)
    )
    return [_out(session, mapping) for mapping in mappings]


def _source_name(session: Session, kind: str, value: str) -> str | None:
    if kind == MappingKind.BUDGET_ENTITY.value:
        return session.scalar(
            select(BudgetExecution.entity_name).where(BudgetExecution.entity_code == value).limit(1)
        )
    for nit, name in session.execute(select(Contract.entity_nit, Contract.entity_name).distinct()):
        if contract_key(nit, name) == value:
            return str(name)
    return None


def _relink(session: Session, kind: str) -> None:
    if kind == MappingKind.BUDGET_ENTITY.value:
        link_budget_institutions(session)
    else:
        link_contract_institutions(session)


@router.post("", response_model=MappingOut, status_code=status.HTTP_201_CREATED)
def create_mapping(body: MappingIn, session: SessionDep, steward: StewardUser) -> MappingOut:
    name = _source_name(session, body.kind, body.source_value)
    if name is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="La entidad de la fuente no existe.")
    if session.get(Institution, body.institution_id) is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="La entidad del directorio no existe."
        )
    exists = session.scalar(
        select(EntityMapping.id).where(
            EntityMapping.kind == body.kind, EntityMapping.source_value == body.source_value
        )
    )
    if exists:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Esta entidad ya tiene un vínculo revisado; elimínelo antes de crear otro.",
        )
    mapping = EntityMapping(
        kind=body.kind,
        source_value=body.source_value,
        source_name=name,
        institution_id=body.institution_id,
        note=" ".join(body.note.split()),
        created_by=steward.id,
    )
    session.add(mapping)
    session.flush()
    audit.record(
        session,
        "entity_mapping_created",
        actor_user_id=steward.id,
        target_type="entity_mapping",
        target_id=str(mapping.id),
        details={
            "kind": body.kind,
            "source_value": body.source_value,
            "institution_id": str(body.institution_id),
        },
    )
    session.commit()
    _relink(session, body.kind)
    return _out(session, mapping)


@router.delete("/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mapping(mapping_id: uuid.UUID, session: SessionDep, steward: StewardUser) -> Response:
    mapping = session.get(EntityMapping, mapping_id)
    if mapping is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Vínculo no encontrado.")
    kind = mapping.kind
    audit.record(
        session,
        "entity_mapping_deleted",
        actor_user_id=steward.id,
        target_type="entity_mapping",
        target_id=str(mapping.id),
        details={
            "kind": kind,
            "source_value": mapping.source_value,
            "institution_id": str(mapping.institution_id),
        },
    )
    session.delete(mapping)
    session.commit()
    _relink(session, kind)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
