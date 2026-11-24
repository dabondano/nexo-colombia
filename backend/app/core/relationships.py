"""The relationship table: every cross-record link that is not a core foreign key
(docs/03-data-model.md, principle 4 and section 3.6). This table is the knowledge graph.

Each link states how much it can be trusted (`confidence_class`) and what kind of
statement it is (`epistemic_label`). A database constraint requires a source record
for every class except `analytical_association`, which requires a method note
instead. Links of class `unverified_claim` are never shown publicly (`public_only`).
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    ColumnElement,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

# Registers core.source_record, which this table's foreign key points at.
import app.sources.models  # noqa: E402, F401
from app.core.db import CORE_SCHEMA, Base
from app.core.labels import ConfidenceClass


class Relationship(Base):
    __tablename__ = "relationship"
    __table_args__ = (
        UniqueConstraint("subject_type", "subject_id", "predicate", "object_type", "object_id"),
        Index("ix_relationship_subject", "subject_type", "subject_id", "predicate"),
        Index("ix_relationship_object", "object_type", "object_id", "predicate"),
        CheckConstraint(
            "(confidence_class <> 'analytical_association' AND source_record_id IS NOT NULL)"
            " OR (confidence_class = 'analytical_association' AND method_note IS NOT NULL)",
            name="relationship_has_source_or_method",
        ),
        {"schema": CORE_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    subject_type: Mapped[str] = mapped_column(String(60))
    subject_id: Mapped[uuid.UUID]
    predicate: Mapped[str] = mapped_column(String(60))
    object_type: Mapped[str] = mapped_column(String(60))
    object_id: Mapped[uuid.UUID]
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    confidence_class: Mapped[str] = mapped_column(String(40))
    epistemic_label: Mapped[str] = mapped_column(String(40))
    # The record the link rests on: the one stating it, or the one it was derived from.
    source_record_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(f"{CORE_SCHEMA}.source_record.id")
    )
    # How NEXO derived the link (required for analytical associations).
    method_note: Mapped[str | None] = mapped_column(Text)
    # The words in the source the link rests on, as published (e.g. an author's name).
    evidence: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


def public_only() -> ColumnElement[bool]:
    """Filter for every public query: unverified claims are never shown."""
    return Relationship.confidence_class != ConfidenceClass.UNVERIFIED_CLAIM.value
