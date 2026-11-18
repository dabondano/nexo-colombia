"""Audit log: an append-only record of security-relevant actions.

Recorded: sign-ins (successful and failed), sign-outs, password changes,
account creation and changes, and data synchronizations. Rows cannot be
updated or deleted: a database trigger (migration "staff accounts and audit
log") rejects both. No IP addresses or user agents are stored.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.db import CORE_SCHEMA, Base


class AuditEvent(Base):
    __tablename__ = "audit_event"
    __table_args__ = {"schema": CORE_SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    # Null for actions by the system or the command line, and for failed sign-ins.
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(f"{CORE_SCHEMA}.user_account.id"), index=True
    )
    action: Mapped[str] = mapped_column(String(60), index=True)
    target_type: Mapped[str | None] = mapped_column(String(60))
    target_id: Mapped[str | None] = mapped_column(String(300))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


def record(
    session: Session,
    action: str,
    *,
    actor_user_id: uuid.UUID | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Add an audit event to the current transaction (the caller commits)."""
    session.add(
        AuditEvent(
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details or {},
        )
    )
