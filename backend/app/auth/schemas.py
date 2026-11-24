"""API schemas for staff accounts."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.auth.models import Role
from app.auth.security import MAX_PASSWORD_LENGTH


class LoginIn(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(max_length=MAX_PASSWORD_LENGTH)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str
    role: Role
    must_change_password: bool
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime


class LoginOut(BaseModel):
    token: str
    expires_at: datetime
    user: UserOut


class PasswordChangeIn(BaseModel):
    current_password: str = Field(max_length=MAX_PASSWORD_LENGTH)
    new_password: str = Field(max_length=MAX_PASSWORD_LENGTH)


class UserCreateIn(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    display_name: str = Field(min_length=1, max_length=200)
    role: Role


class UserUpdateIn(BaseModel):
    role: Role | None = None
    is_active: bool | None = None


class IssuedPassword(BaseModel):
    """A one-time password, shown once to the administrator who issued it."""

    user: UserOut
    temporary_password: str


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    occurred_at: datetime
    actor_user_id: uuid.UUID | None
    actor_email: str | None = None
    action: str
    target_type: str | None
    target_id: str | None
    details: dict[str, Any]


class AuditPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[AuditEventOut]
