"""Password hashing (Argon2id) and session tokens."""

import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_hasher = PasswordHasher()  # Argon2id with the library's current recommended parameters

MIN_PASSWORD_LENGTH = 12
# Argon2 accepts any length; a ceiling keeps a single request from being expensive.
MAX_PASSWORD_LENGTH = 128

# Compared against when the e-mail is unknown, so both cases take the same time.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def password_problem(password: str, email: str) -> str | None:
    """Why a chosen password is not acceptable, in Spanish; None when it is."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres."
    if len(password) > MAX_PASSWORD_LENGTH:
        return f"La contraseña no puede tener más de {MAX_PASSWORD_LENGTH} caracteres."
    if password.casefold() in {email.casefold(), email.split("@")[0].casefold()}:
        return "La contraseña no puede ser el correo."
    if len(set(password)) < 5:
        return "La contraseña repite demasiado los mismos caracteres."
    return None


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def temporary_password() -> str:
    """A one-time password an administrator hands over; the user must replace it."""
    return secrets.token_urlsafe(15)
