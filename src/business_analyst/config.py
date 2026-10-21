
"""Central application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "AI Business Analyst"
    app_env: Literal["development", "test", "staging", "production"] = (
        "development"
    )
    app_debug: bool = False
    log_level: str = "INFO"

    database_url: str = Field(
        default="sqlite:///./business_analyst.db",
        repr=False,
    )

    auth_secret_key: SecretStr = Field(
        default=SecretStr("development-only-change-me"),
        repr=False,
    )
    auth_issuer_url: str | None = None

    ai_provider: str = "disabled"
    ai_api_key: SecretStr | None = Field(default=None, repr=False)
    ai_model: str | None = None

    max_upload_size_mb: int = Field(default=25, ge=1, le=100)
    max_rows: int = Field(default=100_000, ge=1, le=1_000_000)
    max_columns: int = Field(default=200, ge=1, le=2_000)
    temp_file_ttl_minutes: int = Field(default=60, ge=5, le=1_440)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
