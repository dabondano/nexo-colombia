"""Legal reviews of published content (assumption A-007).

A review is pinned to a fingerprint of exactly what was reviewed: for an
article of the Constitution, its current wording version; for a lesson, a
SHA-256 hash of the lesson's content computed by the web server. When the
content changes, the fingerprint no longer matches and pages stop calling the
content reviewed. Reviews are never edited; a new review is a new row.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import CORE_SCHEMA, Base


class ContentType(StrEnum):
    LESSON = "lesson"
    CONSTITUTION_PROVISION = "constitution_provision"


class Decision(StrEnum):
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class ContentReview(Base):
    __tablename__ = "content_review"
    __table_args__ = (
        Index("ix_content_review_content", "content_type", "content_key", "reviewed_at"),
        {"schema": CORE_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    content_type: Mapped[str] = mapped_column(String(40))
    # Lesson slug, or the provision's stable key (e.g. "articulo-11").
    content_key: Mapped[str] = mapped_column(String(200))
    fingerprint: Mapped[str] = mapped_column(String(100))
    decision: Mapped[str] = mapped_column(String(30))
    # Internal: shown to staff only, never on public pages.
    notes: Mapped[str] = mapped_column(Text, default="")
    reviewer_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{CORE_SCHEMA}.user_account.id"), index=True
    )
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
