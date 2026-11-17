"""Public entities (docs/03-data-model.md, section 3.2)."""

from sqlalchemy import Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import CORE_SCHEMA, Base
from app.core.records import CanonicalRecordMixin


class Institution(CanonicalRecordMixin, Base):
    __tablename__ = "institution"
    __table_args__ = (UniqueConstraint("official_code"), {"schema": CORE_SCHEMA})

    # Code assigned by Función Pública (SIGEP).
    official_code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(Text)
    name_normalized: Mapped[str] = mapped_column(Text, index=True)
    nit: Mapped[str | None] = mapped_column(String(20), index=True)
    order: Mapped[str | None] = mapped_column("orden", String(50), index=True)
    suborder: Mapped[str | None] = mapped_column("suborden", String(100))
    level: Mapped[str | None] = mapped_column("nivel", String(100))
    organic_classification: Mapped[str | None] = mapped_column(
        "clasificacion_organica", String(200), index=True
    )
    sector: Mapped[str | None] = mapped_column(String(200))
    legal_nature: Mapped[str | None] = mapped_column("naturaleza_juridica", String(200))
    institution_type: Mapped[str | None] = mapped_column("tipo_institucion", String(100))
    department: Mapped[str | None] = mapped_column("departamento", String(100), index=True)
    municipality: Mapped[str | None] = mapped_column("municipio", String(100))
    website: Mapped[str | None] = mapped_column(Text)
    longitude: Mapped[float | None] = mapped_column(Float)
    latitude: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str | None] = mapped_column("estado", String(50))
