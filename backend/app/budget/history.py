"""Keeps each budget entity's totals per source update date (`budget_snapshot`).

Run after every budget sync. Totals are grouped by the date the source says it
last updated the figures (`source_record.published_at`); running twice for the
same update date overwrites that date's row with the same numbers.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.budget.models import BudgetExecution, BudgetSnapshot
from app.sources.models import SourceRecord

HISTORY_NOTE = (
    "Cada fila son las cifras tal como la fuente las publicó en esa fecha de actualización, "
    "guardadas por NEXO. La fuente no indica la vigencia ni la fecha de corte; si cambia la "
    "vigencia, las cifras vuelven a empezar y la comparación entre filas deja de tener sentido."
)


@dataclass
class _Totals:
    entity_name: str
    appropriation: Decimal = Decimal(0)
    commitments: Decimal = Decimal(0)
    obligations: Decimal = Decimal(0)
    payments: Decimal = Decimal(0)
    line_count: int = 0


def record_snapshots(session: Session) -> int:
    """Stores the current totals; returns the number of entity snapshots written."""
    totals: dict[tuple[str, date], _Totals] = {}
    rows = session.execute(
        select(BudgetExecution, func.date(SourceRecord.published_at)).join(
            SourceRecord, SourceRecord.id == BudgetExecution.source_record_id
        )
    )
    by_entity: dict[str, list[tuple[BudgetExecution, date | None]]] = defaultdict(list)
    for line, published_on in rows:
        by_entity[line.entity_code].append((line, published_on))
    for code, lines in by_entity.items():
        dates = [published_on for _, published_on in lines if published_on is not None]
        if not dates:
            continue  # No update date from the source: nothing honest to key on.
        # One entity, one update date: the latest any of its lines carries.
        key = (code, max(dates))
        entry = totals.setdefault(key, _Totals(entity_name=lines[0][0].entity_name))
        for line, _ in lines:
            entry.appropriation += line.appropriation
            entry.commitments += line.commitments
            entry.obligations += line.obligations
            entry.payments += line.payments
            entry.line_count += 1
    for (code, published_on), entry in totals.items():
        values = {
            "entity_name": entry.entity_name,
            "appropriation": entry.appropriation,
            "commitments": entry.commitments,
            "obligations": entry.obligations,
            "payments": entry.payments,
            "line_count": entry.line_count,
        }
        session.execute(
            insert(BudgetSnapshot)
            .values(entity_code=code, published_on=published_on, **values)
            .on_conflict_do_update(index_elements=["entity_code", "published_on"], set_=values)
        )
    return len(totals)
