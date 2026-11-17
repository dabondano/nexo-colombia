"""Provenance tables: where every record in NEXO comes from.

See docs/03-data-model.md, section 3.1.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import CORE_SCHEMA, Base
from app.core.labels import SyncStatus, VerificationStatus


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Source(Base):
    """An information source in the source registry (brief section 5.3)."""

    __tablename__ = "source"
    __table_args__ = (
        UniqueConstraint("external_ref"),
        CheckConstraint("reliability_class BETWEEN 1 AND 7", name="reliability_class_range"),
        {"schema": CORE_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_uuid)
    # Stable key used by connectors, e.g. "datos.gov.co:h7zv-k39x".
    external_ref: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(300))
    institution: Mapped[str] = mapped_column(String(300))
    url: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100))
    data_types: Mapped[str | None] = mapped_column(Text)
    acquisition_method: Mapped[str] = mapped_column(String(30))
    update_frequency: Mapped[str | None] = mapped_column(String(100))
    reliability_class: Mapped[int] = mapped_column(SmallInteger)
    licence: Mapped[str | None] = mapped_column(String(200))
    access_restrictions: Mapped[str | None] = mapped_column(Text)
    known_limitations: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(
        String(20), default=VerificationStatus.NOT_VERIFIED.value
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    jurisdiction_code: Mapped[str] = mapped_column(String(2), default="CO")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    sync_runs: Mapped[list["SyncRun"]] = relationship(back_populates="source")


class SyncRun(Base):
    """One execution of a connector against a source (brief section 5.6)."""

    __tablename__ = "sync_run"
    __table_args__ = ({"schema": CORE_SCHEMA},)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_uuid)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{CORE_SCHEMA}.source.id"), index=True)
    mode: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default=SyncStatus.RUNNING.value)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rows_seen: Mapped[int] = mapped_column(Integer, default=0)
    rows_new: Mapped[int] = mapped_column(Integer, default=0)
    rows_changed: Mapped[int] = mapped_column(Integer, default=0)
    rows_rejected: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)

    source: Mapped[Source] = relationship(back_populates="sync_runs")


class SourceRecord(Base):
    """The raw item a canonical record was derived from (brief section 5.5).

    Append-only: a changed item at the source creates a new row with a new
    content hash; earlier rows are kept.
    """

    __tablename__ = "source_record"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", "content_hash"),
        {"schema": CORE_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_uuid)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{CORE_SCHEMA}.source.id"), index=True)
    sync_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{CORE_SCHEMA}.sync_run.id"))
    external_id: Mapped[str] = mapped_column(String(300))
    original_url: Mapped[str | None] = mapped_column(Text)
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    content_hash: Mapped[str] = mapped_column(String(64))
    extraction_method: Mapped[str] = mapped_column(String(100))
    # Only fields on the source's allow-list are stored (data minimization).
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    processing_history: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
