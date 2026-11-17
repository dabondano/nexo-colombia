"""Legal instruments and their provisions (docs/03-data-model.md, section 3.3).

An instrument (the Constitution, a law) contains provisions arranged as a tree:
titles, chapters, articles. A provision is the stable identity of, say,
"Artículo 11"; its wording lives in `provision_version`, so a reform adds a
version instead of replacing text.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import CORE_SCHEMA, Base
from app.core.records import CanonicalRecordMixin


class LegalInstrument(CanonicalRecordMixin, Base):
    __tablename__ = "legal_instrument"
    __table_args__ = (UniqueConstraint("slug"), {"schema": CORE_SCHEMA})

    # Stable, readable key used in addresses, e.g. "constitucion-politica-1991".
    slug: Mapped[str] = mapped_column(String(120))
    instrument_type: Mapped[str] = mapped_column(String(40), index=True)
    number: Mapped[str | None] = mapped_column(String(40))
    year: Mapped[int | None] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(Text)
    # 1 is the Constitution; larger numbers are lower in the hierarchy of norms.
    hierarchy_level: Mapped[int] = mapped_column(SmallInteger)
    promulgated_on: Mapped[date | None] = mapped_column(Date)
    official_publication_ref: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(40))
    # What is known about how current the loaded edition is. Shown with every
    # provision, so that an edition is never mistaken for the text in force today.
    edition_note: Mapped[str | None] = mapped_column(Text)


class LegalProvision(CanonicalRecordMixin, Base):
    __tablename__ = "legal_provision"
    __table_args__ = (
        UniqueConstraint("instrument_id", "path"),
        Index("ix_legal_provision_instrument_position", "instrument_id", "position"),
        {"schema": CORE_SCHEMA},
    )

    instrument_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{CORE_SCHEMA}.legal_instrument.id"), index=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(f"{CORE_SCHEMA}.legal_provision.id"), index=True
    )
    # Stable key within the instrument: "articulo-11", "titulo-2/capitulo-1".
    # Articles do not carry their division in the key, so moving an article to
    # another chapter in a later edition does not change its identity.
    path: Mapped[str] = mapped_column(String(300))
    kind: Mapped[str] = mapped_column(String(40))
    # How the provision is cited, e.g. "Artículo 11", "Título II".
    label: Mapped[str] = mapped_column(String(200))
    number: Mapped[str | None] = mapped_column(String(40))
    # The name a division carries, e.g. "De los derechos fundamentales".
    heading: Mapped[str | None] = mapped_column(Text)
    # Reading order within the instrument.
    position: Mapped[int] = mapped_column(Integer)


class ProvisionVersion(Base):
    """The wording of a provision as loaded from one edition.

    The version without `superseded_at` is the one NEXO currently shows.
    `valid_from` and `valid_to` are legal dates and stay empty unless the source
    states them; the moment NEXO noticed a change is not a legal date.
    """

    __tablename__ = "provision_version"
    __table_args__ = (
        # At most one current version per provision.
        Index(
            "uq_provision_version_current",
            "provision_id",
            unique=True,
            postgresql_where=sql_text("superseded_at IS NULL"),
        ),
        {"schema": CORE_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    provision_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{CORE_SCHEMA}.legal_provision.id"), index=True
    )
    # Wording the source presents as in force, without struck-through words.
    # Used for search and excerpts.
    text: Mapped[str] = mapped_column(Text)
    # Everything the source prints for the provision, in order, each piece marked
    # as wording, editor's note, or wording printed after the mark "TEXTO
    # ANTERIOR" (see app/law/constitution.py). Pages show wording and notes apart.
    segments: Mapped[list[dict[str, str]]] = mapped_column(JSONB, default=list)
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{CORE_SCHEMA}.source_record.id"), index=True
    )
