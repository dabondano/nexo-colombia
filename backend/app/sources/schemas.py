"""API schemas for the source registry."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SyncRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    mode: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    rows_seen: int
    rows_new: int
    rows_changed: int
    rows_rejected: int


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    external_ref: str
    name: str
    institution: str
    url: str
    category: str
    acquisition_method: str
    update_frequency: str | None
    reliability_class: int
    licence: str | None
    known_limitations: str | None
    verification_status: str
    last_verified_at: datetime | None
    last_successful_sync: SyncRunOut | None = None
