"""Public, read-only endpoints for national budget execution ("Presupuesto").

Rates are computed from the published figures (owner decision of 2026-11-18):
commitments, obligations and payments divided by the current appropriation.
Lists are alphabetical; nothing is ranked.
"""

import uuid
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Response
from pydantic import BaseModel
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session

from app.budget.history import HISTORY_NOTE
from app.budget.links import LINK_RULE, institution_for_budget_entity
from app.budget.models import BudgetExecution, BudgetSnapshot
from app.core.db import get_session
from app.core.labels import DataQualityStatus, EpistemicLabel
from app.core.listing import (
    DEFAULT_LIMIT,
    FilterOption,
    FilterParam,
    LimitParam,
    OffsetParam,
    SearchParam,
    contains_all_words,
    filter_options,
)
from app.core.provenance import ProvenanceOut, load_provenance
from app.sources.models import SourceRecord

router = APIRouter(prefix="/budget", tags=["budget"])
SessionDep = Annotated[Session, Depends(get_session)]
CodeParam = Annotated[str, Path(max_length=30, pattern=r"^[0-9A-Za-z-]+$")]

RATE_FORMULA = (
    "Porcentaje = valor de la etapa ÷ apropiación vigente × 100, calculado por NEXO con las "
    "cifras publicadas. Compromisos: recursos ya comprometidos (por ejemplo, contratos); "
    "obligaciones: bienes y servicios recibidos que deben pagarse; pagos: lo efectivamente girado."
)
YEAR_NOTE = (
    "La fuente no indica la vigencia ni la fecha de corte de estas cifras; solo la fecha de su "
    "última actualización, que se muestra con cada registro. Cada actualización reemplaza las "
    "cifras anteriores."
)


class Amounts(BaseModel):
    appropriation: Decimal
    commitments: Decimal
    obligations: Decimal
    payments: Decimal


class Rates(BaseModel):
    """Shares of the appropriation, between 0 and 1; null when the appropriation is zero."""

    commitments: Decimal | None
    obligations: Decimal | None
    payments: Decimal | None


def _rates(amounts: Amounts) -> Rates:
    def share(value: Decimal) -> Decimal | None:
        if amounts.appropriation == 0:
            return None
        return (value / amounts.appropriation).quantize(Decimal("0.0001"), ROUND_HALF_UP)

    return Rates(
        commitments=share(amounts.commitments),
        obligations=share(amounts.obligations),
        payments=share(amounts.payments),
    )


def _sums() -> list[ColumnElement[Any]]:
    return [
        func.sum(BudgetExecution.appropriation).label("appropriation"),
        func.sum(BudgetExecution.commitments).label("commitments"),
        func.sum(BudgetExecution.obligations).label("obligations"),
        func.sum(BudgetExecution.payments).label("payments"),
    ]


def _amounts(row: Any) -> Amounts:
    return Amounts(
        appropriation=row.appropriation or Decimal(0),
        commitments=row.commitments or Decimal(0),
        obligations=row.obligations or Decimal(0),
        payments=row.payments or Decimal(0),
    )


class SectorTotal(BaseModel):
    sector_name: str | None
    entity_count: int
    amounts: Amounts
    rates: Rates


class BudgetSummary(BaseModel):
    entity_count: int
    row_count: int
    amounts: Amounts
    rates: Rates
    source_updated_at: datetime | None
    sectors: list[SectorTotal]
    rate_formula: str = RATE_FORMULA
    year_note: str = YEAR_NOTE
    rates_label: EpistemicLabel = EpistemicLabel.HECHO_DOCUMENTADO


class EntityBudget(BaseModel):
    entity_code: str
    entity_name: str
    sector_name: str | None
    amounts: Amounts
    rates: Rates


class EntityBudgetPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[EntityBudget]


class BudgetLine(BaseModel):
    funding_source: str | None
    funds_situation: str | None
    budget_resource: str | None
    amounts: Amounts
    rates: Rates
    data_quality_status: str


class LinkedInstitutionOut(BaseModel):
    institution_id: uuid.UUID
    name: str


class SnapshotOut(BaseModel):
    published_on: date
    amounts: Amounts
    rates: Rates


class EntityBudgetOut(EntityBudget):
    sector_code: str | None
    # An analytical association computed by NEXO (A-014), not part of the source.
    linked_institution: LinkedInstitutionOut | None = None
    linked_institution_label: EpistemicLabel = EpistemicLabel.HIPOTESIS_ANALITICA
    linked_institution_rule: str = LINK_RULE
    # Totals per source update date, oldest first (A-011: not a fiscal period).
    history: list[SnapshotOut] = []
    history_note: str = HISTORY_NOTE
    lines: list[BudgetLine]
    data_quality_status: str
    epistemic_label: EpistemicLabel = EpistemicLabel.HECHO_DOCUMENTADO
    provenance: ProvenanceOut
    rate_formula: str = RATE_FORMULA
    year_note: str = YEAR_NOTE


class BudgetFilters(BaseModel):
    sector: list[FilterOption]


@router.get("/summary", response_model=BudgetSummary)
def budget_summary(session: SessionDep) -> BudgetSummary:
    totals = session.execute(
        select(
            func.count(func.distinct(BudgetExecution.entity_code)).label("entities"),
            func.count().label("rows"),
            *_sums(),
        )
    ).one()
    updated = session.scalar(
        select(func.max(SourceRecord.published_at)).join(
            BudgetExecution, BudgetExecution.source_record_id == SourceRecord.id
        )
    )
    sectors = session.execute(
        select(
            BudgetExecution.sector_name,
            func.count(func.distinct(BudgetExecution.entity_code)).label("entities"),
            *_sums(),
        )
        .group_by(BudgetExecution.sector_name)
        .order_by(BudgetExecution.sector_name)
    ).all()
    amounts = _amounts(totals)
    return BudgetSummary(
        entity_count=totals.entities,
        row_count=totals.rows,
        amounts=amounts,
        rates=_rates(amounts),
        source_updated_at=updated,
        sectors=[
            SectorTotal(
                sector_name=row.sector_name,
                entity_count=row.entities,
                amounts=_amounts(row),
                rates=_rates(_amounts(row)),
            )
            for row in sectors
        ],
    )


@router.get("/filters", response_model=BudgetFilters)
def budget_filters(session: SessionDep) -> BudgetFilters:
    return BudgetFilters(sector=filter_options(session, BudgetExecution.sector_name))


@router.get("/entities", response_model=EntityBudgetPage)
def list_entities(
    session: SessionDep,
    q: SearchParam = None,
    sector: FilterParam = None,
    limit: LimitParam = DEFAULT_LIMIT,
    offset: OffsetParam = 0,
) -> EntityBudgetPage:
    grouped = select(
        BudgetExecution.entity_code,
        func.min(BudgetExecution.entity_name).label("entity_name"),
        func.min(BudgetExecution.entity_name_normalized).label("name_normalized"),
        func.min(BudgetExecution.sector_name).label("sector_name"),
        *_sums(),
    ).group_by(BudgetExecution.entity_code)
    if q:
        grouped = grouped.where(*contains_all_words(BudgetExecution.entity_name_normalized, q))
    if sector:
        grouped = grouped.where(BudgetExecution.sector_name == sector)
    subquery = grouped.subquery()
    total = session.scalar(select(func.count()).select_from(subquery)) or 0
    # Alphabetical order: a neutral ordering that ranks no entity above another.
    rows = session.execute(
        select(subquery)
        .order_by(subquery.c.name_normalized, subquery.c.entity_code)
        .limit(limit)
        .offset(offset)
    ).all()
    return EntityBudgetPage(
        total=total,
        limit=limit,
        offset=offset,
        items=[
            EntityBudget(
                entity_code=row.entity_code,
                entity_name=row.entity_name,
                sector_name=row.sector_name,
                amounts=_amounts(row),
                rates=_rates(_amounts(row)),
            )
            for row in rows
        ],
    )


@router.head("/entities/{entity_code}", include_in_schema=False)
def entity_exists(entity_code: CodeParam, session: SessionDep) -> Response:
    """Existence check without the record body, used by the web app to answer 404 early."""
    found = session.scalar(
        select(BudgetExecution.id).where(BudgetExecution.entity_code == entity_code).limit(1)
    )
    return Response(status_code=200 if found else 404)


QUALITY_ORDER = [
    DataQualityStatus.CONFLICTING.value,
    DataQualityStatus.INCOMPLETE.value,
    DataQualityStatus.STALE.value,
    DataQualityStatus.ACCEPTABLE.value,
    DataQualityStatus.VERIFIED.value,
]


@router.get("/entities/{entity_code}", response_model=EntityBudgetOut)
def get_entity(entity_code: CodeParam, session: SessionDep) -> EntityBudgetOut:
    records = list(
        session.scalars(
            select(BudgetExecution)
            .where(BudgetExecution.entity_code == entity_code)
            .order_by(
                BudgetExecution.funding_source,
                BudgetExecution.funds_situation,
                BudgetExecution.budget_resource,
            )
        )
    )
    if not records:
        raise HTTPException(status_code=404, detail="Entidad sin datos de presupuesto")
    lines = []
    for record in records:
        amounts = Amounts(
            appropriation=record.appropriation,
            commitments=record.commitments,
            obligations=record.obligations,
            payments=record.payments,
        )
        lines.append(
            BudgetLine(
                funding_source=record.funding_source,
                funds_situation=record.funds_situation,
                budget_resource=record.budget_resource,
                amounts=amounts,
                rates=_rates(amounts),
                data_quality_status=record.data_quality_status,
            )
        )
    totals = Amounts(
        appropriation=sum((line.amounts.appropriation for line in lines), Decimal(0)),
        commitments=sum((line.amounts.commitments for line in lines), Decimal(0)),
        obligations=sum((line.amounts.obligations for line in lines), Decimal(0)),
        payments=sum((line.amounts.payments for line in lines), Decimal(0)),
    )
    first = records[0]
    # The most recently acquired line carries the provenance shown for the entity.
    latest = max(records, key=lambda record: record.updated_at)
    return EntityBudgetOut(
        entity_code=first.entity_code,
        entity_name=first.entity_name,
        sector_code=first.sector_code,
        sector_name=first.sector_name,
        amounts=totals,
        rates=_rates(totals),
        lines=lines,
        data_quality_status=min(
            (record.data_quality_status for record in records), key=QUALITY_ORDER.index
        ),
        linked_institution=(
            LinkedInstitutionOut(institution_id=linked.institution_id, name=linked.name)
            if (linked := institution_for_budget_entity(session, first.entity_code))
            else None
        ),
        linked_institution_rule=linked.rule if linked else LINK_RULE,
        history=[_snapshot(snapshot) for snapshot in _history(session, first.entity_code)],
        provenance=load_provenance(session, latest.source_record_id),
    )


def _history(session: Session, entity_code: str) -> list[BudgetSnapshot]:
    return list(
        session.scalars(
            select(BudgetSnapshot)
            .where(BudgetSnapshot.entity_code == entity_code)
            .order_by(BudgetSnapshot.published_on)
        )
    )


def _snapshot(snapshot: BudgetSnapshot) -> SnapshotOut:
    amounts = Amounts(
        appropriation=snapshot.appropriation,
        commitments=snapshot.commitments,
        obligations=snapshot.obligations,
        payments=snapshot.payments,
    )
    return SnapshotOut(published_on=snapshot.published_on, amounts=amounts, rates=_rates(amounts))
