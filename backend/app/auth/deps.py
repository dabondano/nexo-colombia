"""Authentication and role checks for API routes.

The web application calls the API from its server with the session token in
an `Authorization: Bearer` header; the browser only holds that token in an
HTTP-only cookie on the web application's own domain. The API reads no
cookies, so requests from other sites cannot use a signed-in session (no CSRF).
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.models import Role, UserAccount
from app.auth.service import resolve
from app.core.db import get_session

_bearer = HTTPBearer(auto_error=False)

SessionDep = Annotated[Session, Depends(get_session)]
CredentialsDep = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]

UNAUTHENTICATED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Debe iniciar sesión.",
    headers={"WWW-Authenticate": "Bearer"},
)


def session_token(credentials: CredentialsDep) -> str:
    if credentials is None or not credentials.credentials:
        raise UNAUTHENTICATED
    return credentials.credentials


TokenDep = Annotated[str, Depends(session_token)]


def current_user(session: SessionDep, token: TokenDep) -> UserAccount:
    user = resolve(session, token)
    if user is None:
        raise UNAUTHENTICATED
    return user


CurrentUser = Annotated[UserAccount, Depends(current_user)]


def require_roles(*roles: Role) -> Callable[[UserAccount], UserAccount]:
    """A dependency that admits only the given roles; administrators are always admitted."""
    allowed = {Role.ADMIN.value, *(role.value for role in roles)}

    def check(user: CurrentUser) -> UserAccount:
        if user.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Su rol no permite esta acción.")
        if user.must_change_password:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail="Debe cambiar su contraseña antes de continuar."
            )
        return user

    return check
