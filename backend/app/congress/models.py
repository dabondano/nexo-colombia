"""People and the public positions they hold (docs/03-data-model.md, section 3.2).

A `person` is permanent; a `position_holding` is a dated fact about that person,
taken from one source. Only members of the Cámara de Representantes are loaded
for now (source S-010).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import CORE_SCHEMA, Base
from app.core.records import CanonicalRecordMixin


class Person(Base):
    __tablename__ = "person"
    __table_args__ = {"schema": CORE_SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(Text)
    name_normalized: Mapped[str] = mapped_column(Text, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PositionHolding(CanonicalRecordMixin, Base):
    __tablename__ = "position_holding"
    __table_args__ = (UniqueConstraint("source_key"), {"schema": CORE_SCHEMA})

    # Stable identifier at the source: the member's institutional e-mail address.
    source_key: Mapped[str] = mapped_column(String(300))
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{CORE_SCHEMA}.person.id"), index=True)
    position: Mapped[str] = mapped_column(String(200))
    corporation: Mapped[str] = mapped_column(String(200))
    # The period as the source names it, e.g. "2026-2027".
    period: Mapped[str] = mapped_column(String(20), index=True)
    constituency: Mapped[str | None] = mapped_column(String(200), index=True)
    # Party, movement or organization as published, not linked to an organization record.
    party: Mapped[str | None] = mapped_column(Text, index=True)
    # Legal basis of the seat when the source gives one instead of a party (opposition seat).
    seat_basis: Mapped[str | None] = mapped_column(Text)
    # Institutional contact details published by the Cámara (owner decision of 2026-11-18).
    email: Mapped[str | None] = mapped_column(String(300))
    office: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
