"""Shared pytest fixtures."""

import pytest

from business_analyst.config import Settings


@pytest.fixture
def test_settings() -> Settings:
    """Return isolated settings for unit tests."""
    return Settings(
        app_env="test",
        app_debug=False,
        database_url="sqlite:///:memory:",
        auth_secret_key="test-only-secret-not-for-production",
        ai_provider="disabled",
        max_upload_size_mb=5,
        max_rows=1_000,
        max_columns=50,
    )