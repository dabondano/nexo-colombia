"""API schemas for unified search."""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


class SearchHit(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    record_type: str
    record_id: uuid.UUID
    # The key in the record's public address: its id, or the budget code for a
    # budget entity (whose pages are addressed by code).
    record_key: str = ""
    title: str
    summary: str | None
    record_date: date | None


class TypeCount(BaseModel):
    record_type: str
    count: int


class SearchPage(BaseModel):
    query: str
    total: int
    limit: int
    offset: int
    # Matches per record type for the same words and dates, ignoring the type filter.
    counts: list[TypeCount]
    items: list[SearchHit]
