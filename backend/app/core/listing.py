"""Helpers shared by the public list endpoints: paging, text search, filter options."""

from typing import Annotated, Any

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import ColumnElement, Select, func, select
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.ingestion.text import normalize_for_search

DEFAULT_LIMIT = 25
MAX_LIMIT = 100

LimitParam = Annotated[int, Query(ge=1, le=MAX_LIMIT, description="Registros por página")]
OffsetParam = Annotated[int, Query(ge=0, description="Registros a omitir")]
SearchParam = Annotated[str | None, Query(max_length=200, description="Texto a buscar")]
FilterParam = Annotated[str | None, Query(max_length=300)]


class FilterOption(BaseModel):
    value: str
    count: int


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def contains_all_words(
    column: InstrumentedAttribute[str] | InstrumentedAttribute[str | None], text: str
) -> list[ColumnElement[bool]]:
    """Conditions requiring every word of `text` to appear in an accent-free column."""
    words = normalize_for_search(text).split()
    return [column.like(f"%{_escape_like(word)}%", escape="\\") for word in words]


def count_rows(session: Session, statement: Select[Any]) -> int:
    return session.scalar(select(func.count()).select_from(statement.subquery())) or 0


def filter_options(
    session: Session, column: InstrumentedAttribute[str | None]
) -> list[FilterOption]:
    """Distinct values of a column with the number of records that carry each."""
    rows = session.execute(
        select(column, func.count()).where(column.is_not(None)).group_by(column).order_by(column)
    )
    return [FilterOption(value=value, count=count) for value, count in rows]
