"""Data-quality monitoring for the staff panel (Phase 3).

For every source NEXO has loaded: the last sync, when the publisher last
updated the data, how the published records are rated, and plain checks that
point the data steward at something to look at. The checks compare each load
with the previous successful one, so a source that always rejects the same
share of rows (the Cámara representatives, A-011) is not flagged every week.
"""

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.budget.models import BudgetExecution
from app.catalog.models import Institution
from app.congress.models import PositionHolding
from app.core.labels import SyncStatus
from app.law.models import LegalInstrument, LegalProvision
from app.legislation.models import LegislativeInitiative
from app.procurement.models import Contract
from app.sources.models import Source, SourceRecord, SyncRun

CANONICAL_MODELS: tuple[Any, ...] = (
    Institution,
    LegislativeInitiative,
    PositionHolding,
    BudgetExecution,
    Contract,
    LegalInstrument,
    LegalProvision,
)
# The scheduled synchronization runs weekly (.github/workflows/sync.yml).
STALE_AFTER = timedelta(days=8)
ROW_DROP = 0.10
REJECT_RATE_RISE = 0.02
MIN_REJECTS = 10


@dataclass
class SourceQuality:
    source_id: uuid.UUID
    name: str
    external_ref: str
    last_run: SyncRun
    last_success_at: datetime | None
    source_updated_at: datetime | None
    records_by_quality: dict[str, int] = field(default_factory=dict)
    checks: list[str] = field(default_factory=list)


def _rate(run: SyncRun) -> float:
    return run.rows_rejected / run.rows_seen if run.rows_seen else 0.0


def _checks(runs: list[SyncRun], now: datetime) -> list[str]:
    last = runs[0]
    succeeded = [run for run in runs if run.status == SyncStatus.SUCCEEDED.value]
    checks: list[str] = []
    if last.status == SyncStatus.FAILED.value:
        checks.append(f"La última sincronización falló: {last.error or 'sin detalle'}.")
    if not succeeded:
        checks.append("Ninguna sincronización ha terminado bien.")
        return checks
    latest = succeeded[0]
    finished = latest.finished_at or latest.started_at
    if now - finished > STALE_AFTER:
        checks.append(
            f"La última carga correcta fue hace {(now - finished).days} días; "
            "la sincronización programada es semanal."
        )
    if len(succeeded) > 1:
        previous = succeeded[1]
        if previous.rows_seen and latest.rows_seen < previous.rows_seen * (1 - ROW_DROP):
            drop = 1 - latest.rows_seen / previous.rows_seen
            checks.append(
                f"La fuente entregó {latest.rows_seen:,} filas, {drop:.0%} menos que en la carga "
                f"anterior ({previous.rows_seen:,}).".replace(",", ".")
            )
        if (
            latest.rows_rejected >= MIN_REJECTS
            and _rate(latest) > _rate(previous) + REJECT_RATE_RISE
        ):
            checks.append(
                f"Las filas rechazadas subieron al {_rate(latest):.1%} "
                f"(antes {_rate(previous):.1%}); revise los motivos en la sincronización."
            )
    return checks


def data_quality(session: Session, now: datetime | None = None) -> list[SourceQuality]:
    now = now or datetime.now(UTC)
    runs_by_source: dict[uuid.UUID, list[SyncRun]] = defaultdict(list)
    for run in session.scalars(select(SyncRun).order_by(SyncRun.started_at.desc())):
        runs_by_source[run.source_id].append(run)
    if not runs_by_source:
        return []

    quality: dict[uuid.UUID, dict[str, int]] = defaultdict(dict)
    for model in CANONICAL_MODELS:
        rows = session.execute(
            select(SourceRecord.source_id, model.data_quality_status, func.count())
            .join(SourceRecord, SourceRecord.id == model.source_record_id)
            .group_by(SourceRecord.source_id, model.data_quality_status)
        )
        for source_id, status, count in rows:
            bucket = quality[source_id]
            bucket[status] = bucket.get(status, 0) + count

    updated = dict(
        session.execute(
            select(SourceRecord.source_id, func.max(SourceRecord.published_at)).group_by(
                SourceRecord.source_id
            )
        ).all()
    )
    sources = session.scalars(select(Source).where(Source.id.in_(runs_by_source))).all()
    result = []
    for source in sorted(sources, key=lambda s: s.name):
        runs = runs_by_source[source.id]
        success = next((r for r in runs if r.status == SyncStatus.SUCCEEDED.value), None)
        result.append(
            SourceQuality(
                source_id=source.id,
                name=source.name,
                external_ref=source.external_ref,
                last_run=runs[0],
                last_success_at=(success.finished_at or success.started_at) if success else None,
                source_updated_at=updated.get(source.id),
                records_by_quality=quality.get(source.id, {}),
                checks=_checks(runs, now),
            )
        )
    return result
