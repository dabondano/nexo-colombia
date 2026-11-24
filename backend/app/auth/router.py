"""Staff sign-in and account endpoints (`/auth`) and administration (`/admin`)."""

import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.auth.deps import CurrentUser, SessionDep, TokenDep, require_roles
from app.auth.models import Role, UserAccount
from app.auth.schemas import (
    AuditEventOut,
    AuditPage,
    IssuedPassword,
    LoginIn,
    LoginOut,
    PasswordChangeIn,
    UserCreateIn,
    UserOut,
    UserUpdateIn,
)
from app.auth.security import hash_password, password_problem, temporary_password, verify_password
from app.auth.service import normalize_email, revoke_all_sessions, sign_in, sign_out
from app.core import audit
from app.core.audit import AuditEvent
from app.core.listing import LimitParam, OffsetParam
from app.sources.models import Source, SyncReject, SyncRun
from app.sources.quality import data_quality, database_size

auth_router = APIRouter(prefix="/auth", tags=["auth"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])

AdminUser = Annotated[UserAccount, Depends(require_roles())]
StewardUser = Annotated[UserAccount, Depends(require_roles(Role.DATA_STEWARD))]

SIGN_IN_FAILED = "Correo o contraseña incorrectos, o la cuenta no está disponible."


@auth_router.post("/login", response_model=LoginOut)
def login(body: LoginIn, session: SessionDep) -> LoginOut:
    result = sign_in(session, body.email, body.password)
    if result is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=SIGN_IN_FAILED)
    return LoginOut(
        token=result.token,
        expires_at=result.expires_at,
        user=UserOut.model_validate(result.user),
    )


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(session: SessionDep, token: TokenDep, user: CurrentUser) -> Response:
    sign_out(session, token, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@auth_router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserAccount:
    return user


@auth_router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: PasswordChangeIn, session: SessionDep, token: TokenDep, user: CurrentUser
) -> Response:
    if not verify_password(user.password_hash, body.current_password):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="La contraseña actual no es correcta."
        )
    problem = password_problem(body.new_password, user.email)
    if problem is None and body.new_password == body.current_password:
        problem = "La nueva contraseña debe ser distinta de la actual."
    if problem:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=problem)
    user.password_hash = hash_password(body.new_password)
    user.must_change_password = False
    revoke_all_sessions(session, user.id, keep_token=token)
    audit.record(session, "password_changed", actor_user_id=user.id)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Administration -------------------------------------------------------


@admin_router.get("/users", response_model=list[UserOut])
def list_users(session: SessionDep, _admin: AdminUser) -> list[UserAccount]:
    return list(session.scalars(select(UserAccount).order_by(UserAccount.email)))


@admin_router.post("/users", response_model=IssuedPassword, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreateIn, session: SessionDep, admin: AdminUser) -> IssuedPassword:
    password = temporary_password()
    user = UserAccount(
        email=normalize_email(body.email),
        display_name=body.display_name.strip(),
        role=body.role.value,
        password_hash=hash_password(password),
        must_change_password=True,
    )
    session.add(user)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="Ya existe una cuenta con ese correo."
        ) from None
    audit.record(
        session,
        "user_created",
        actor_user_id=admin.id,
        target_type="user_account",
        target_id=str(user.id),
        details={"email": user.email, "role": user.role},
    )
    session.commit()
    return IssuedPassword(user=UserOut.model_validate(user), temporary_password=password)


def _get_user(session: SessionDep, user_id: uuid.UUID) -> UserAccount:
    user = session.get(UserAccount, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada.")
    return user


def _active_admins(session: SessionDep) -> int:
    return (
        session.scalar(
            select(func.count())
            .select_from(UserAccount)
            .where(UserAccount.role == Role.ADMIN.value, UserAccount.is_active.is_(True))
        )
        or 0
    )


@admin_router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: uuid.UUID, body: UserUpdateIn, session: SessionDep, admin: AdminUser
) -> UserAccount:
    user = _get_user(session, user_id)
    changes: dict[str, Any] = {}
    if body.role is not None and body.role.value != user.role:
        changes["role"] = {"from": user.role, "to": body.role.value}
        user.role = body.role.value
    if body.is_active is not None and body.is_active != user.is_active:
        changes["is_active"] = {"from": user.is_active, "to": body.is_active}
        user.is_active = body.is_active
    if not changes:
        return user
    session.flush()
    if _active_admins(session) == 0:
        session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="Debe quedar al menos un administrador activo."
        )
    revoke_all_sessions(session, user.id)
    audit.record(
        session,
        "user_updated",
        actor_user_id=admin.id,
        target_type="user_account",
        target_id=str(user.id),
        details=changes,
    )
    session.commit()
    return user


@admin_router.post("/users/{user_id}/reset-password", response_model=IssuedPassword)
def reset_password(user_id: uuid.UUID, session: SessionDep, admin: AdminUser) -> IssuedPassword:
    user = _get_user(session, user_id)
    password = temporary_password()
    user.password_hash = hash_password(password)
    user.must_change_password = True
    user.failed_attempts = 0
    user.locked_until = None
    revoke_all_sessions(session, user.id)
    audit.record(
        session,
        "password_reset",
        actor_user_id=admin.id,
        target_type="user_account",
        target_id=str(user.id),
    )
    session.commit()
    return IssuedPassword(user=UserOut.model_validate(user), temporary_password=password)


@admin_router.get("/audit", response_model=AuditPage)
def audit_log(
    session: SessionDep,
    _admin: AdminUser,
    action: Annotated[str | None, Query(max_length=60)] = None,
    limit: LimitParam = 50,
    offset: OffsetParam = 0,
) -> AuditPage:
    statement = select(AuditEvent, UserAccount.email).outerjoin(
        UserAccount, UserAccount.id == AuditEvent.actor_user_id
    )
    if action:
        statement = statement.where(AuditEvent.action == action)
    total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = session.execute(
        statement.order_by(AuditEvent.occurred_at.desc(), AuditEvent.id).limit(limit).offset(offset)
    ).all()
    items = []
    for event, email in rows:
        item = AuditEventOut.model_validate(event)
        item.actor_email = email
        items.append(item)
    return AuditPage(total=total, limit=limit, offset=offset, items=items)


# --- Synchronizations (data stewards) --------------------------------------


class SyncRunOut(BaseModel):
    id: uuid.UUID
    source_name: str
    source_ref: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    rows_seen: int
    rows_new: int
    rows_changed: int
    rows_rejected: int
    error: str | None


class SyncRunPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[SyncRunOut]


class SyncRejectOut(BaseModel):
    id: uuid.UUID
    external_id: str | None
    reason: str
    payload: dict[str, Any]


class SyncRejectPage(BaseModel):
    run: SyncRunOut
    total: int
    limit: int
    offset: int
    items: list[SyncRejectOut]


def _run_out(run: SyncRun, source: Source) -> SyncRunOut:
    return SyncRunOut(
        id=run.id,
        source_name=source.name,
        source_ref=source.external_ref,
        status=run.status,
        started_at=run.started_at,
        finished_at=run.finished_at,
        rows_seen=run.rows_seen,
        rows_new=run.rows_new,
        rows_changed=run.rows_changed,
        rows_rejected=run.rows_rejected,
        error=run.error,
    )


@admin_router.get("/sync-runs", response_model=SyncRunPage)
def sync_runs(
    session: SessionDep, _steward: StewardUser, limit: LimitParam = 50, offset: OffsetParam = 0
) -> SyncRunPage:
    total = session.scalar(select(func.count()).select_from(SyncRun)) or 0
    rows = session.execute(
        select(SyncRun, Source)
        .join(Source, Source.id == SyncRun.source_id)
        .order_by(SyncRun.started_at.desc(), SyncRun.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return SyncRunPage(
        total=total, limit=limit, offset=offset, items=[_run_out(r, s) for r, s in rows]
    )


class SourceQualityOut(BaseModel):
    source_id: uuid.UUID
    name: str
    external_ref: str
    last_run: SyncRunOut
    last_success_at: datetime | None
    source_updated_at: datetime | None
    records_by_quality: dict[str, int]
    checks: list[str]


@admin_router.get("/data-quality", response_model=list[SourceQualityOut])
def source_quality(session: SessionDep, _steward: StewardUser) -> list[SourceQualityOut]:
    sources = {source.id: source for source in session.scalars(select(Source))}
    return [
        SourceQualityOut(
            source_id=item.source_id,
            name=item.name,
            external_ref=item.external_ref,
            last_run=_run_out(item.last_run, sources[item.source_id]),
            last_success_at=item.last_success_at,
            source_updated_at=item.source_updated_at,
            records_by_quality=item.records_by_quality,
            checks=item.checks,
        )
        for item in data_quality(session)
    ]


class DatabaseSizeOut(BaseModel):
    used_mb: float
    limit_mb: int
    check: str | None


@admin_router.get("/database-size", response_model=DatabaseSizeOut)
def database_size_endpoint(session: SessionDep, _steward: StewardUser) -> DatabaseSizeOut:
    size = database_size(session)
    return DatabaseSizeOut(used_mb=size.used_mb, limit_mb=size.limit_mb, check=size.check)


@admin_router.get("/sync-runs/{run_id}/rejects", response_model=SyncRejectPage)
def sync_rejects(
    run_id: uuid.UUID,
    session: SessionDep,
    _steward: StewardUser,
    limit: LimitParam = 50,
    offset: OffsetParam = 0,
) -> SyncRejectPage:
    row = session.execute(
        select(SyncRun, Source)
        .join(Source, Source.id == SyncRun.source_id)
        .where(SyncRun.id == run_id)
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Sincronización no encontrada.")
    total = (
        session.scalar(
            select(func.count()).select_from(SyncReject).where(SyncReject.sync_run_id == run_id)
        )
        or 0
    )
    rejects = session.scalars(
        select(SyncReject)
        .where(SyncReject.sync_run_id == run_id)
        .order_by(SyncReject.external_id, SyncReject.id)
        .limit(limit)
        .offset(offset)
    )
    return SyncRejectPage(
        run=_run_out(*row),
        total=total,
        limit=limit,
        offset=offset,
        items=[
            SyncRejectOut(id=r.id, external_id=r.external_id, reason=r.reason, payload=r.payload)
            for r in rejects
        ],
    )
