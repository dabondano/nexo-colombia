"""Public contracts from SECOP II (source S-001, docs/03-data-model.md `contract`).

One record per contract (`id_contrato`). Natural persons who are suppliers are
not named or identified (A-015): only suppliers identified by a NIT keep their
name and NIT. Names and ID numbers of officials, supervisors and legal
representatives, and all bank fields, are never downloaded.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import CORE_SCHEMA, Base
from app.core.records import CanonicalRecordMixin

MONEY = Numeric(20, 2)


class Contract(CanonicalRecordMixin, Base):
    __tablename__ = "contract"
    __table_args__ = (UniqueConstraint("source_key"), {"schema": CORE_SCHEMA})

    source_key: Mapped[str] = mapped_column(String(60))  # id_contrato, e.g. CO1.PCCNTR.9605165
    process_id: Mapped[str | None] = mapped_column(String(60))
    reference: Mapped[str | None] = mapped_column(String(200))
    entity_name: Mapped[str] = mapped_column(Text)
    entity_nit: Mapped[str | None] = mapped_column(String(20), index=True)
    # Set by the NIT rule (A-016), in app/procurement/links.py; null when no single match.
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(f"{CORE_SCHEMA}.institution.id", ondelete="SET NULL"), index=True
    )
    department: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    sector: Mapped[str | None] = mapped_column(String(200))
    branch: Mapped[str | None] = mapped_column(String(60))
    status: Mapped[str | None] = mapped_column(String(60), index=True)
    contract_type: Mapped[str | None] = mapped_column(String(100), index=True)
    modality: Mapped[str | None] = mapped_column(String(120), index=True)
    modality_reason: Mapped[str | None] = mapped_column(Text)
    purpose: Mapped[str] = mapped_column(Text)
    purpose_normalized: Mapped[str] = mapped_column(Text)
    signed_on: Mapped[date] = mapped_column(Date, index=True)
    start_on: Mapped[date | None] = mapped_column(Date)
    end_on: Mapped[date | None] = mapped_column(Date)
    duration_text: Mapped[str | None] = mapped_column(String(60))
    days_added: Mapped[int | None]
    # "empresa" (identified by NIT), "persona_natural", or "sin_definir".
    supplier_kind: Mapped[str] = mapped_column(String(20))
    supplier_name: Mapped[str | None] = mapped_column(Text)
    supplier_nit: Mapped[str | None] = mapped_column(String(20))
    supplier_is_sme: Mapped[bool | None] = mapped_column(Boolean)
    resource_origin: Mapped[str | None] = mapped_column(String(100))
    spending_type: Mapped[str | None] = mapped_column(String(60))
    # Pesos, as published.
    value: Mapped[Decimal] = mapped_column(MONEY)
    invoiced: Mapped[Decimal | None] = mapped_column(MONEY)
    paid: Mapped[Decimal | None] = mapped_column(MONEY)
    pending_payment: Mapped[Decimal | None] = mapped_column(MONEY)
    pending_execution: Mapped[Decimal | None] = mapped_column(MONEY)
    process_url: Mapped[str | None] = mapped_column(Text)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
