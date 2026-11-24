"""Removes contracts that have left the loading window (A-015).

Owner decision of 2026-11-24: NEXO keeps only SECOP II contracts signed in the
last `settings.secop_window_days` days, so the database fits the free plan.
This is the one exception to the append-only raw layer (ADR-004): the raw
copies of removed contracts are deleted too, by the database function
core.prune_contract_raw_records, which only the database owner could write and
which can only delete SECOP raw records whose contract is no longer in NEXO.
SECOP itself keeps every contract.
"""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.ingestion.datasets.contracts import window_start
from app.procurement.models import Contract
from app.search.indexing import CONTRACT
from app.search.models import SearchDocument


@dataclass(frozen=True)
class PruneResult:
    window_start: date
    contracts: int
    raw_records: int


def prune_contracts(session: Session, today: date | None = None) -> PruneResult:
    start = window_start(today)
    old = select(Contract.id).where(Contract.signed_on < start)
    session.execute(
        delete(SearchDocument).where(
            SearchDocument.record_type == CONTRACT, SearchDocument.record_id.in_(old)
        )
    )
    removed = session.execute(delete(Contract).where(Contract.signed_on < start))
    raw = session.scalar(text("SELECT core.prune_contract_raw_records()")) or 0
    session.commit()
    return PruneResult(
        window_start=start,
        contracts=removed.rowcount,  # type: ignore[attr-defined]
        raw_records=raw,
    )
