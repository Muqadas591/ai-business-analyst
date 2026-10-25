import pytest

from business_analyst.security.identity import (
    AuthenticatedPrincipal,
    IdentityError,
    require_authenticated_user_id,
)


def test_verified_principal_returns_user_id():
    principal = AuthenticatedPrincipal(user_id="user-123")

    assert require_authenticated_user_id(principal) == "user-123"


def test_missing_principal_is_rejected():
    with pytest.raises(IdentityError):
        require_authenticated_user_id(None)


def test_blank_identity_is_rejected():
    principal = AuthenticatedPrincipal(user_id="  ")

    with pytest.raises(IdentityError):
        require_authenticated_user_id(principal)


def test_oversized_identity_is_rejected():
    principal = AuthenticatedPrincipal(user_id="u" * 256)

    with pytest.raises(IdentityError):
        require_authenticated_user_id(principal)
