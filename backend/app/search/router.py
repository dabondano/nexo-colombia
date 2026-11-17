"""Unified search across record types ("Observatorio", PRD FR-OBS-01)."""

from datetime import date
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.core.listing import DEFAULT_LIMIT, LimitParam, OffsetParam
from app.ingestion.text import normalize_for_search
from app.search.indexing import INSTITUTION, LEGISLATIVE_INITIATIVE, RECORD_TYPES, TEXT_CONFIG
from app.search.models import SearchDocument
from app.search.schemas import SearchHit, SearchPage, TypeCount

router = APIRouter(prefix="/search", tags=["search"])

SessionDep = Annotated[Session, Depends(get_session)]
RecordType = Literal["institution", "legislative_initiative"]

assert set(RecordType.__args__) == {INSTITUTION, LEGISLATIVE_INITIATIVE}  # type: ignore[attr-defined]


def _query(text: str) -> ColumnElement[Any]:
    """The words searched, prepared like the indexed text (no accents or capitals).

    `websearch_to_tsquery` never raises on user input. It requires every word,
    and understands quoted phrases, "or" and a leading minus sign.
    """
    return func.websearch_to_tsquery(TEXT_CONFIG, normalize_for_search(text))


@router.get("", response_model=SearchPage)
def search(
    session: SessionDep,
    q: Annotated[str, Query(min_length=1, max_length=200, description="Texto a buscar")],
    record_type: Annotated[RecordType | None, Query(alias="type")] = None,
    date_from: Annotated[date | None, Query(description="Fecha del registro, desde")] = None,
    date_to: Annotated[date | None, Query(description="Fecha del registro, hasta")] = None,
    limit: LimitParam = DEFAULT_LIMIT,
    offset: OffsetParam = 0,
) -> SearchPage:
    text = " ".join(q.split())
    query = _query(text)
    empty = SearchPage(query=text, total=0, limit=limit, offset=offset, counts=[], items=[])
    # Only stop words ("de", "la") or punctuation: nothing to search for.
    if not text or not session.scalar(select(func.numnode(query))):
        return empty

    conditions: list[ColumnElement[bool]] = [SearchDocument.tsv.op("@@")(query)]
    # A date range only applies to records that carry a date.
    if date_from:
        conditions.append(SearchDocument.record_date >= date_from)
    if date_to:
        conditions.append(SearchDocument.record_date <= date_to)

    by_type: dict[str, int] = {
        record_type_: count
        for record_type_, count in session.execute(
            select(SearchDocument.record_type, func.count())
            .where(*conditions)
            .group_by(SearchDocument.record_type)
        )
    }
    counts = [TypeCount(record_type=t, count=by_type[t]) for t in RECORD_TYPES if t in by_type]

    if record_type:
        conditions.append(SearchDocument.record_type == record_type)
        total = by_type.get(record_type, 0)
    else:
        total = sum(by_type.values())

    # Results are ordered only by how well the text matches the words searched
    # (names and numbers count more than supporting text), then alphabetically.
    rank = func.ts_rank_cd(SearchDocument.tsv, query, 1)
    rows = session.scalars(
        select(SearchDocument)
        .where(*conditions)
        .order_by(rank.desc(), SearchDocument.title, SearchDocument.record_id)
        .limit(limit)
        .offset(offset)
    ).all()
    return SearchPage(
        query=text,
        total=total,
        limit=limit,
        offset=offset,
        counts=counts,
        items=[SearchHit.model_validate(row) for row in rows],
    )
