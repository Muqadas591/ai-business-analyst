"""Trusted identity boundary for protected application operations."""

from __future__ import annotations

from dataclasses import dataclass


class IdentityError(PermissionError):
    """Raised when a trusted authenticated identity is missing or invalid."""


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    """Identity established by a trusted authentication provider."""

    user_id: str


def require_authenticated_user_id(
    principal: AuthenticatedPrincipal | None,
) -> str:
    """Return the verified user ID or reject the operation.

    Do not construct this principal from a user-controlled form field.
    Build it only after your authentication provider verifies the session
    or token.
    """
    if principal is None:
        raise IdentityError("Authentication is required.")

    user_id = principal.user_id

    if not isinstance(user_id, str) or not user_id.strip():
        raise IdentityError("Authentication is required.")

    normalized = user_id.strip()

    if len(normalized) > 255:
        raise IdentityError("Invalid authenticated identity.")

    if any(ord(character) < 32 for character in normalized):
        raise IdentityError("Invalid authenticated identity.")

    return normalized
