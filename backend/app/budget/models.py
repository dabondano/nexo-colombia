"""Budget execution of the national budget (docs/03-data-model.md, `budget_execution`).

One record per entity, funding source, funds situation and budget resource, as
published by MinHacienda (source S-005). The source does not state the fiscal
year or the cut-off date (owner decision of 2026-11-18: say so, assert neither);
the record's provenance carries the date the source last updated it. Earlier
figures stay in the append-only raw layer, and each entity's totals per
source update date are kept in `budget_snapshot` to show change over time.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import CORE_SCHEMA, Base
from app.core.records import CanonicalRecordMixin

MONEY = Numeric(20, 2)


class BudgetExecution(CanonicalRecordMixin, Base):
    __tablename__ = "budget_execution"
    __table_args__ = (UniqueConstraint("source_key"), {"schema": CORE_SCHEMA})

    source_key: Mapped[str] = mapped_column(String(400))
    entity_code: Mapped[str] = mapped_column(String(30), index=True)
    entity_name: Mapped[str] = mapped_column(Text)
    entity_name_normalized: Mapped[str] = mapped_column(Text)
    sector_code: Mapped[str | None] = mapped_column(String(10))
    sector_name: Mapped[str | None] = mapped_column(String(200), index=True)
    funding_source: Mapped[str | None] = mapped_column(String(100))
    funds_situation: Mapped[str | None] = mapped_column(String(20))
    budget_resource: Mapped[str | None] = mapped_column(String(200))
    # Pesos, as published.
    appropriation: Mapped[Decimal] = mapped_column(MONEY)
    commitments: Mapped[Decimal] = mapped_column(MONEY)
    obligations: Mapped[Decimal] = mapped_column(MONEY)
    payments: Mapped[Decimal] = mapped_column(MONEY)


class BudgetSnapshot(Base):
    """An entity's totals as published on one source update date, kept across updates.

    `budget_execution` holds only the latest figures, because each source update
    replaces the previous one. After every budget sync NEXO stores each entity's
    totals under the date the source says it last updated them, so the change
    between updates can be shown. The date is the publisher's update date, not a
    fiscal period or cut-off (the source states neither, A-011).
    """

    __tablename__ = "budget_snapshot"
    __table_args__ = (
        UniqueConstraint("entity_code", "published_on"),
        {"schema": CORE_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entity_code: Mapped[str] = mapped_column(String(30), index=True)
    entity_name: Mapped[str] = mapped_column(Text)
    published_on: Mapped[date] = mapped_column(Date)
    appropriation: Mapped[Decimal] = mapped_column(MONEY)
    commitments: Mapped[Decimal] = mapped_column(MONEY)
    obligations: Mapped[Decimal] = mapped_column(MONEY)
    payments: Mapped[Decimal] = mapped_column(MONEY)
    line_count: Mapped[int] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
