"""Columns shared by every canonical record."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import CORE_SCHEMA
from app.core.labels import DataQualityStatus


class CanonicalRecordMixin:
    """Identity, jurisdiction, provenance link and data-quality status.

    `source_record_id` points at the latest raw item the record was derived
    from. Earlier versions stay in `core.source_record`, which is append-only.
    """

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    jurisdiction_code: Mapped[str] = mapped_column(String(2), default="CO")
    source_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{CORE_SCHEMA}.source_record.id"), index=True
    )
    data_quality_status: Mapped[str] = mapped_column(
        String(20), default=DataQualityStatus.ACCEPTABLE.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
