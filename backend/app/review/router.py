"""Endpoints for legal reviews.

- Staff (legal reviewers and administrators): record a review, read the history.
- Public: the latest decision per item with its date and fingerprint, without
  notes or the reviewer's identity.
"""

import re
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.deps import SessionDep, require_roles
from app.auth.models import Role, UserAccount
from app.core import audit
from app.law.models import LegalInstrument, LegalProvision, ProvisionVersion
from app.review.models import ContentReview, ContentType, Decision

CONSTITUTION_SLUG = "constitucion-politica-1991"
LESSON_KEY = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

staff_router = APIRouter(prefix="/reviews", tags=["review"])
public_router = APIRouter(prefix="/reviews", tags=["review"])

ReviewerUser = Annotated[UserAccount, Depends(require_roles(Role.LEGAL_REVIEWER))]


class ReviewIn(BaseModel):
    content_type: ContentType
    content_key: str = Field(min_length=1, max_length=200)
    # Required for lessons (computed by the web server); ignored for provisions,
    # whose fingerprint the API takes from the current wording.
    fingerprint: str | None = Field(default=None, max_length=100)
    decision: Decision
    notes: str = Field(default="", max_length=5000)


class ReviewOut(BaseModel):
    id: uuid.UUID
    content_type: ContentType
    content_key: str
    fingerprint: str
    decision: Decision
    notes: str
    reviewer_email: str | None
    reviewer_name: str | None
    reviewed_at: datetime


class PublicReview(BaseModel):
    content_type: ContentType
    content_key: str
    fingerprint: str
    decision: Decision
    reviewed_at: datetime


def current_provision_fingerprint(session: Session, key: str) -> str | None:
    """The id of the provision's current wording, or None if there is no such provision."""
    version_id = session.scalar(
        select(ProvisionVersion.id)
        .join(LegalProvision, LegalProvision.id == ProvisionVersion.provision_id)
        .join(LegalInstrument, LegalInstrument.id == LegalProvision.instrument_id)
        .where(
            LegalInstrument.slug == CONSTITUTION_SLUG,
            LegalProvision.path == key,
            ProvisionVersion.superseded_at.is_(None),
        )
    )
    return str(version_id) if version_id else None


@staff_router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def record_review(body: ReviewIn, session: SessionDep, reviewer: ReviewerUser) -> ReviewOut:
    if body.content_type is ContentType.CONSTITUTION_PROVISION:
        fingerprint = current_provision_fingerprint(session, body.content_key)
        if fingerprint is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Disposición no encontrada.")
    else:
        if not LESSON_KEY.fullmatch(body.content_key):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Lección no válida.")
        if body.fingerprint is None or not SHA256.fullmatch(body.fingerprint):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Falta la huella del contenido."
            )
        fingerprint = body.fingerprint
    if body.decision is Decision.CHANGES_REQUESTED and not body.notes.strip():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Explique en las notas qué debe cambiar."
        )
    review = ContentReview(
        content_type=body.content_type.value,
        content_key=body.content_key,
        fingerprint=fingerprint,
        decision=body.decision.value,
        notes=body.notes.strip(),
        reviewer_user_id=reviewer.id,
    )
    session.add(review)
    session.flush()
    audit.record(
        session,
        "review_recorded",
        actor_user_id=reviewer.id,
        target_type=body.content_type.value,
        target_id=body.content_key,
        details={"decision": body.decision.value, "fingerprint": fingerprint},
    )
    session.commit()
    return ReviewOut(
        id=review.id,
        content_type=ContentType(review.content_type),
        content_key=review.content_key,
        fingerprint=review.fingerprint,
        decision=Decision(review.decision),
        notes=review.notes,
        reviewer_email=reviewer.email,
        reviewer_name=reviewer.display_name,
        reviewed_at=review.reviewed_at,
    )


@staff_router.get("", response_model=list[ReviewOut])
def review_history(
    session: SessionDep,
    _reviewer: ReviewerUser,
    content_type: ContentType,
    content_key: Annotated[str, Query(max_length=200)],
) -> list[ReviewOut]:
    rows = session.execute(
        select(ContentReview, UserAccount)
        .join(UserAccount, UserAccount.id == ContentReview.reviewer_user_id)
        .where(
            ContentReview.content_type == content_type.value,
            ContentReview.content_key == content_key,
        )
        .order_by(ContentReview.reviewed_at.desc(), ContentReview.id)
    ).all()
    return [
        ReviewOut(
            id=review.id,
            content_type=ContentType(review.content_type),
            content_key=review.content_key,
            fingerprint=review.fingerprint,
            decision=Decision(review.decision),
            notes=review.notes,
            reviewer_email=user.email,
            reviewer_name=user.display_name,
            reviewed_at=review.reviewed_at,
        )
        for review, user in rows
    ]


@public_router.get("/latest", response_model=list[PublicReview])
def latest_reviews(
    session: SessionDep,
    content_type: ContentType,
    content_key: Annotated[str | None, Query(max_length=200)] = None,
) -> list[PublicReview]:
    """The latest review of each item of a type (or of one item)."""
    ranked = select(
        ContentReview,
        func.row_number()
        .over(
            partition_by=ContentReview.content_key,
            order_by=(ContentReview.reviewed_at.desc(), ContentReview.id.desc()),
        )
        .label("rank"),
    ).where(ContentReview.content_type == content_type.value)
    if content_key is not None:
        ranked = ranked.where(ContentReview.content_key == content_key)
    subquery = ranked.subquery()
    rows = session.execute(
        select(subquery).where(subquery.c.rank == 1).order_by(subquery.c.content_key)
    ).all()
    return [
        PublicReview(
            content_type=ContentType(row.content_type),
            content_key=row.content_key,
            fingerprint=row.fingerprint,
            decision=Decision(row.decision),
            reviewed_at=row.reviewed_at,
        )
        for row in rows
    ]
