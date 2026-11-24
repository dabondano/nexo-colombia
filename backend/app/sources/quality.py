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

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.budget.models import BudgetExecution
from app.catalog.models import Institution
from app.congress.models import PositionHolding
from app.core.config import get_settings
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


# Warn when the database uses this share of the plan's storage.
SIZE_WARNING_SHARE = 0.8


@dataclass(frozen=True)
class DatabaseSize:
    used_mb: float
    limit_mb: int
    check: str | None


def database_size(session: Session) -> DatabaseSize:
    used = session.scalar(text("SELECT pg_database_size(current_database())")) or 0
    used_mb = round(used / 1024 / 1024, 1)
    limit = get_settings().database_size_limit_mb
    check = None
    if used_mb >= limit * SIZE_WARNING_SHARE:
        check = (
            f"La base de datos ocupa {used_mb:.0f} MB de {limit} MB ({used_mb / limit:.0%}). "
            "Reduzca la ventana de contratos (NEXO_SECOP_WINDOW_DAYS) o amplíe el plan."
        )
    return DatabaseSize(used_mb=used_mb, limit_mb=limit, check=check)


def report(session: Session, now: datetime | None = None) -> str | None:
    """Markdown listing every check, or None when there is nothing to look at."""
    lines: list[str] = []
    size = database_size(session)
    if size.check:
        lines += ["### Base de datos", "", f"- {size.check}", ""]
    for item in data_quality(session, now):
        if item.checks:
            lines += [f"### {item.name}", "", *(f"- {check}" for check in item.checks), ""]
    if not lines:
        return None
    header = [
        "Avisos de la revisión automática de calidad de los datos, después de la "
        "sincronización. Más detalle en el panel del equipo, «Calidad de los datos».",
        "",
    ]
    return "\n".join(header + lines)


def main(argv: list[str]) -> int:
    """Usage:  python -m app.sources.quality [--report FILE]

    Prints the checks. With --report, writes them as Markdown to FILE, and only
    when there is something to look at, so a workflow can open an issue then.
    """
    from app.core.db import get_engine

    with Session(get_engine()) as session:
        text_report = report(session)
    print(text_report or "Sin avisos de calidad de los datos.")
    if text_report and len(argv) == 2 and argv[0] == "--report":
        with open(argv[1], "w", encoding="utf-8") as handle:
            handle.write(text_report)
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
