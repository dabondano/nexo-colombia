"""Signing in and out, sessions, and the lockout rule.

- Five consecutive failed sign-ins lock the account for 15 minutes. The
  answer to a failed sign-in is the same whether the e-mail is unknown, the
  password is wrong, the account is inactive or it is locked, so the form
  does not reveal which accounts exist.
- A session lasts at most 12 hours and ends after 2 hours without use.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth.models import AuthSession, UserAccount
from app.auth.security import (
    hash_password,
    needs_rehash,
    new_token,
    token_hash,
    verify_password,
)
from app.core import audit

MAX_FAILED_ATTEMPTS = 5
LOCKOUT = timedelta(minutes=15)
SESSION_LIFETIME = timedelta(hours=12)
IDLE_TIMEOUT = timedelta(hours=2)
# last_seen_at is written at most this often, to avoid a write on every request.
TOUCH_INTERVAL = timedelta(minutes=5)


@dataclass(frozen=True)
class SignIn:
    token: str
    user: UserAccount
    expires_at: datetime


def normalize_email(email: str) -> str:
    return email.strip().lower()


def sign_in(
    session: Session, email: str, password: str, now: datetime | None = None
) -> SignIn | None:
    now = now or datetime.now(UTC)
    address = normalize_email(email)
    user = session.scalar(select(UserAccount).where(UserAccount.email == address))
    password_ok = verify_password(user.password_hash if user else None, password)

    if user is None:
        audit.record(session, "sign_in_failed", details={"reason": "unknown_email"})
        session.commit()
        return None
    locked = user.locked_until is not None and user.locked_until > now
    if not user.is_active or locked or not password_ok:
        reason = "inactive" if not user.is_active else "locked" if locked else "wrong_password"
        if reason == "wrong_password":
            user.failed_attempts += 1
            if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = now + LOCKOUT
                user.failed_attempts = 0
                reason = "wrong_password_locked"
        audit.record(
            session,
            "sign_in_failed",
            target_type="user_account",
            target_id=str(user.id),
            details={"reason": reason},
        )
        session.commit()
        return None

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    user.failed_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    token = new_token()
    expires_at = now + SESSION_LIFETIME
    session.add(
        AuthSession(
            user_id=user.id, token_hash=token_hash(token), last_seen_at=now, expires_at=expires_at
        )
    )
    audit.record(session, "sign_in", actor_user_id=user.id)
    session.commit()
    return SignIn(token=token, user=user, expires_at=expires_at)


def resolve(session: Session, token: str, now: datetime | None = None) -> UserAccount | None:
    """The active user of a valid session token, or None."""
    now = now or datetime.now(UTC)
    row = session.execute(
        select(AuthSession, UserAccount)
        .join(UserAccount, UserAccount.id == AuthSession.user_id)
        .where(AuthSession.token_hash == token_hash(token))
    ).first()
    if row is None:
        return None
    auth_session, user = row
    if (
        auth_session.revoked_at is not None
        or auth_session.expires_at <= now
        or auth_session.last_seen_at + IDLE_TIMEOUT <= now
        or not user.is_active
    ):
        return None
    if now - auth_session.last_seen_at >= TOUCH_INTERVAL:
        auth_session.last_seen_at = now
        session.commit()
    return user


def sign_out(session: Session, token: str, user_id: uuid.UUID) -> None:
    session.execute(
        update(AuthSession)
        .where(AuthSession.token_hash == token_hash(token), AuthSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    audit.record(session, "sign_out", actor_user_id=user_id)
    session.commit()


def revoke_all_sessions(
    session: Session, user_id: uuid.UUID, keep_token: str | None = None
) -> None:
    """End every session of a user (after a password or role change), optionally but one."""
    statement = update(AuthSession).where(
        AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None)
    )
    if keep_token is not None:
        statement = statement.where(AuthSession.token_hash != token_hash(keep_token))
    session.execute(statement.values(revoked_at=datetime.now(UTC)))
