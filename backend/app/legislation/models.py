"""Legislative initiatives (docs/03-data-model.md, section 3.3)."""

from datetime import date

from sqlalchemy import Date, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import CORE_SCHEMA, Base
from app.core.records import CanonicalRecordMixin


class LegislativeInitiative(CanonicalRecordMixin, Base):
    __tablename__ = "legislative_initiative"
    __table_args__ = (UniqueConstraint("source_key"), {"schema": CORE_SCHEMA})

    # Stable identifier of the initiative at its source (the Cámara page URL).
    source_key: Mapped[str] = mapped_column(Text)
    camara_number: Mapped[str | None] = mapped_column(String(100), index=True)
    senado_number: Mapped[str | None] = mapped_column(String(100), index=True)
    camara_filed_on: Mapped[date | None] = mapped_column(Date)
    senado_filed_on: Mapped[date | None] = mapped_column(Date)
    short_title: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    title_normalized: Mapped[str] = mapped_column(Text)
    purpose: Mapped[str | None] = mapped_column(Text)
    observations: Mapped[str | None] = mapped_column(Text)
    law_type: Mapped[str | None] = mapped_column(String(100), index=True)
    # Authors exactly as published; not yet linked to person records.
    authors_text: Mapped[str | None] = mapped_column(Text)
    authors_normalized: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(100), index=True)
    origin_chamber: Mapped[str | None] = mapped_column(String(50))
    commission: Mapped[str | None] = mapped_column(Text, index=True)
    legislature: Mapped[str | None] = mapped_column(String(20), index=True)
