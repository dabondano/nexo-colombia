"""Unified search across record types ("Observatorio", PRD FR-OBS-01)."""

from datetime import date
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session

from app.budget.models import BudgetExecution
from app.core.db import get_session
from app.core.listing import DEFAULT_LIMIT, LimitParam, OffsetParam
from app.ingestion.datasets.constitution import SLUG as CONSTITUTION_SLUG
from app.ingestion.text import normalize_for_search
from app.law.models import LegalInstrument, LegalProvision
from app.search.indexing import BUDGET_ENTITY, LEGAL_PROVISION, RECORD_TYPES, TEXT_CONFIG
from app.search.models import SearchDocument
from app.search.schemas import SearchHit, SearchPage, TypeCount

router = APIRouter(prefix="/search", tags=["search"])

SessionDep = Annotated[Session, Depends(get_session)]
RecordType = Literal[
    "legal_provision",
    "legislative_initiative",
    "representative",
    "institution",
    "budget_entity",
    "contract",
]

assert set(RecordType.__args__) == set(RECORD_TYPES)  # type: ignore[attr-defined]


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

    # Results are ordered only by how well the text matches the words searched:
    # first the records whose title contains every word ("artículo 86" finds the
    # article before bills that mention it), then by how well the rest matches
    # (names and numbers count more than supporting text), then alphabetically.
    in_title = SearchDocument.title_tsv.op("@@")(query)
    rank = func.ts_rank_cd(SearchDocument.tsv, query, 1)
    rows = session.scalars(
        select(SearchDocument)
        .where(*conditions)
        .order_by(in_title.desc(), rank.desc(), SearchDocument.title, SearchDocument.record_id)
        .limit(limit)
        .offset(offset)
    ).all()
    provision_ids = [row.record_id for row in rows if row.record_type == LEGAL_PROVISION]
    provision_keys = (
        {
            provision_id: (
                f"constitucion/{path}" if slug == CONSTITUTION_SLUG else f"leyes/{slug}/{path}"
            )
            for provision_id, slug, path in session.execute(
                select(LegalProvision.id, LegalInstrument.slug, LegalProvision.path)
                .join(LegalInstrument, LegalInstrument.id == LegalProvision.instrument_id)
                .where(LegalProvision.id.in_(provision_ids))
            )
        }
        if provision_ids
        else {}
    )
    budget_ids = [row.record_id for row in rows if row.record_type == BUDGET_ENTITY]
    budget_codes: dict[Any, str] = {
        line_id: code
        for line_id, code in session.execute(
            select(BudgetExecution.id, BudgetExecution.entity_code).where(
                BudgetExecution.id.in_(budget_ids)
            )
        )
    }
    items = []
    for row in rows:
        hit = SearchHit.model_validate(row)
        hit.record_key = provision_keys.get(row.record_id) or budget_codes.get(
            row.record_id, str(row.record_id)
        )
        items.append(hit)
    return SearchPage(
        query=text,
        total=total,
        limit=limit,
        offset=offset,
        counts=counts,
        items=items,
    )
