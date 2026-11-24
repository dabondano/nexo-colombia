"""Entity links reviewed by the data team (assumption A-017).

The automatic rules link a budget entity to the directory by exact name (A-014)
and a contract's entity by NIT (A-016). They leave many entities unlinked on
purpose rather than guess. A data steward can link one of those by hand, with a
note saying what the decision rests on; the linkers apply these mappings before
their own rule, every change is in the audit log, and pages say the link was
reviewed by NEXO's team, not published by a source.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import CORE_SCHEMA, Base
from app.ingestion.text import normalize_name

MANUAL_RULE = (
    "Vínculo revisado por el equipo de datos de NEXO: las fuentes no comparten un código que "
    "permita enlazarlos automáticamente, y una persona del equipo comprobó que se trata de la "
    "misma entidad. Es una asociación analítica, no un dato oficial. Motivo registrado: {note}"
)


class MappingKind(StrEnum):
    # source_value: the budget code, e.g. "13-01-01".
    BUDGET_ENTITY = "budget_entity"
    # source_value: contract_key(nit, entity name) as published in SECOP II.
    CONTRACT_ENTITY = "contract_entity"


def contract_key(nit: str | None, entity_name: str) -> str:
    # Imported here: app.procurement imports this module's model through the linkers.
    from app.procurement.links import nit_key

    return f"{nit_key(nit) or ''}|{normalize_name(entity_name)}"


class EntityMapping(Base):
    __tablename__ = "entity_mapping"
    __table_args__ = (UniqueConstraint("kind", "source_value"), {"schema": CORE_SCHEMA})

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(String(30))
    source_value: Mapped[str] = mapped_column(String(400))
    # The entity's name as the source publishes it, for people reading the list.
    source_name: Mapped[str] = mapped_column(Text)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{CORE_SCHEMA}.institution.id", ondelete="CASCADE"), index=True
    )
    note: Mapped[str] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(f"{CORE_SCHEMA}.user_account.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
