"""Create the first administrator account.

Usage:  python -m app.auth.cli create-admin EMAIL "Display name"

Prints a one-time password; the administrator must replace it at first sign-in.
Further accounts are created from the staff panel.
"""

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import Role, UserAccount
from app.auth.security import hash_password, temporary_password
from app.auth.service import normalize_email
from app.core import audit
from app.core.db import get_engine


def create_admin(session: Session, email: str, display_name: str) -> str:
    address = normalize_email(email)
    if session.scalar(select(UserAccount.id).where(UserAccount.email == address)) is not None:
        raise SystemExit(f"Ya existe una cuenta con el correo {address}.")
    password = temporary_password()
    user = UserAccount(
        email=address,
        display_name=display_name.strip(),
        role=Role.ADMIN.value,
        password_hash=hash_password(password),
        must_change_password=True,
    )
    session.add(user)
    session.flush()
    audit.record(
        session,
        "user_created",
        target_type="user_account",
        target_id=str(user.id),
        details={"email": address, "role": Role.ADMIN.value, "via": "command_line"},
    )
    session.commit()
    return password


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[0] != "create-admin" or "@" not in argv[1]:
        print(__doc__)
        return 2
    with Session(get_engine()) as session:
        password = create_admin(session, argv[1], argv[2])
    print(f"Cuenta de administración creada para {normalize_email(argv[1])}.")
    print(f"Contraseña de un solo uso (cámbiela al ingresar): {password}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
