"""Search index derived from the canonical records (docs/02-architecture.md, 5.2).

One row per searchable record of any type. The table can be rebuilt at any
time from `core` (see app/search/reindex.py), so it holds no facts of its own.
"""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, Index, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import SEARCH_SCHEMA, Base


class SearchDocument(Base):
    __tablename__ = "document"
    __table_args__ = (
        UniqueConstraint("record_type", "record_id"),
        Index("ix_document_tsv", "tsv", postgresql_using="gin"),
        {"schema": SEARCH_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    record_type: Mapped[str] = mapped_column(String(40), index=True)
    record_id: Mapped[uuid.UUID] = mapped_column()
    # What a result shows: the record's name and one line of context.
    title: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    # The date a record is filtered by, when it has one (a bill's filing date).
    record_date: Mapped[date | None] = mapped_column(Date, index=True)
    jurisdiction_code: Mapped[str] = mapped_column(String(2), default="CO")
    tsv: Mapped[Any] = mapped_column(TSVECTOR)
    # The title alone, prepared like `tsv`. Records whose title contains every
    # word searched are listed first (app/search/router.py).
    title_tsv: Mapped[Any] = mapped_column(TSVECTOR, server_default=text("''::tsvector"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
