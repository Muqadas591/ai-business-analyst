"""Central application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
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
    app_env: Literal["development", "test", "staging", "production"] = "development"
    app_debug: bool = False
    log_level: str = "INFO"

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/ai_business_analyst",
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
        # Database connection management
    db_pool_size: int = Field(default=3, ge=1, le=20)
    db_max_overflow: int = Field(default=2, ge=0, le=20)
    db_pool_timeout_seconds: int = Field(default=30, ge=1, le=120)
    db_pool_recycle_seconds: int = Field(default=1800, ge=60, le=7200)
    db_connect_timeout_seconds: int = Field(default=10, ge=1, le=60)
    csv_sample_bytes: int = Field(default=65_536, ge=1_024, le=262_144)
    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Reject unsafe configuration when running in production."""
        if self.app_env != "production":
            return self

        if self.app_debug:
            raise ValueError(
                "APP_DEBUG must be false in production."
            )

        secret = self.auth_secret_key.get_secret_value()

        if (
            len(secret) < 32
            or secret == "development-only-change-me"
            or secret == "replace_with_a_secure_random_secret"
        ):
            raise ValueError(
                "AUTH_SECRET_KEY must be a strong, unique secret "
                "of at least 32 characters in production."
            )

        return self

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
