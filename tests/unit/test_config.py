
"""Tests for application configuration."""

from business_analyst.config import Settings


def test_default_settings_are_safe_for_local_development() -> None:
    settings = Settings(
        _env_file=None,
        app_env="test",
        ai_provider="disabled",
    )

    assert settings.app_name == "AI Business Analyst"
    assert settings.app_env == "test"
    assert settings.ai_provider == "disabled"
    assert settings.max_upload_size_mb > 0
    assert settings.max_rows > 0


def test_resource_limits_can_be_configured() -> None:
    settings = Settings(
        _env_file=None,
        max_upload_size_mb=5,
        max_rows=1000,
        max_columns=50,
    )

    assert settings.max_upload_size_mb == 5
    assert settings.max_rows == 1000
    assert settings.max_columns == 50
