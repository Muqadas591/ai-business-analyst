"""Application registration, login, and password verification."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from business_analyst.auth_models import AppUser
from business_analyst.workspaces.access import WorkspaceAccessService

_USERNAME_PATTERN = re.compile(r"^[a-z0-9_.-]{3,32}$")

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_LENGTH = 16
_KEY_LENGTH = 64


class AuthenticationError(Exception):
    """Raised when authentication or registration fails."""


def normalize_username(username: str) -> str:
    """Normalize and validate a username."""
    if not isinstance(username, str):
        raise ValueError("Username must be text.")

    normalized = username.strip().lower()

    if not _USERNAME_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Username must contain 3–32 characters: "
            "lowercase letters, numbers, periods, underscores, or hyphens."
        )

    return normalized


def validate_password(password: str) -> None:
    """Apply baseline password requirements."""
    if not isinstance(password, str):
        raise ValueError("Password must be text.")

    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")

    if len(password) > 1024:
        raise ValueError("Password is too long.")


def hash_password(password: str) -> str:
    """Hash a password using a unique salt and scrypt."""
    validate_password(password)

    salt = secrets.token_bytes(_SALT_LENGTH)

    derived_key = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_KEY_LENGTH,
    )

    return f"scrypt${salt.hex()}${derived_key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password without storing or comparing plaintext passwords."""
    if not isinstance(password, str) or not isinstance(stored_hash, str):
        return False

    try:
        algorithm, salt_hex, expected_hex = stored_hash.split("$")

        if algorithm != "scrypt":
            return False

        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(expected_hex)

        if len(salt) != _SALT_LENGTH or len(expected_key) != _KEY_LENGTH:
            return False

        actual_key = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=_SCRYPT_N,
            r=_SCRYPT_R,
            p=_SCRYPT_P,
            dklen=_KEY_LENGTH,
        )

        return hmac.compare_digest(actual_key, expected_key)

    except (ValueError, TypeError):
        return False


def register_user(
    session: Session,
    *,
    username: str,
    password: str,
) -> AppUser:
    """Register a user and create their first workspace atomically."""
    clean_username = normalize_username(username)
    password_hash = hash_password(password)

    existing_user = session.scalar(
        select(AppUser).where(func.lower(AppUser.username) == clean_username)
    )

    if existing_user is not None:
        raise AuthenticationError("Unable to register with that username.")

    try:
        user = AppUser(
            username=clean_username,
            password_hash=password_hash,
            is_active=True,
        )
        session.add(user)
        session.flush()

        # Create the workspace and owner membership in the same transaction.
        access = WorkspaceAccessService(session)
        access.create_workspace(
            authenticated_user_id=user.id,
            name=f"{clean_username}'s Workspace",
        )

        session.commit()
        return user

    except Exception:
        session.rollback()
        raise


def authenticate_user(
    session: Session,
    *,
    username: str,
    password: str,
) -> AppUser:
    """Authenticate an active user with username and password."""
    try:
        clean_username = normalize_username(username)
    except ValueError:
        raise AuthenticationError("Invalid username or password.") from None

    user = session.scalar(
        select(AppUser).where(func.lower(AppUser.username) == clean_username)
    )

    if (
        user is None
        or not user.is_active
        or not verify_password(password, user.password_hash)
    ):
        raise AuthenticationError("Invalid username or password.")

    return user
