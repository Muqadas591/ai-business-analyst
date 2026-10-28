"""Alembic migration environment for AI Business Analyst."""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool

# Project root: directory containing pyproject.toml and app.py.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

# Allow Alembic to import the application package.
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from business_analyst.auth_models import AuthBase
from business_analyst.config import get_settings
from business_analyst.workspaces.models import WorkspaceBase

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use the same database configuration as the application.
settings = get_settings()
database_url = settings.database_url

if not database_url:
    raise RuntimeError(
        "DATABASE_URL is missing. Configure it in application settings "
        "or the root .env file."
    )

# Escape percent signs for ConfigParser interpolation.
config.set_main_option(
    "sqlalchemy.url",
    database_url.replace("%", "%%"),
)

# Include all SQLAlchemy model metadata used by the database schema.
target_metadata = [
    WorkspaceBase.metadata,
    AuthBase.metadata,
]


def run_migrations_offline() -> None:
    """Generate migration SQL without opening a database connection."""
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a dedicated database connection."""
    url = config.get_main_option("sqlalchemy.url")

    connect_args = (
        {"check_same_thread": False}
        if url.startswith("sqlite:")
        else {"connect_timeout": settings.db_connect_timeout_seconds}
    )

    migration_engine = create_engine(
        url,
        poolclass=pool.NullPool,
        connect_args=connect_args,
        pool_pre_ping=True,
    )

    try:
        with migration_engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        migration_engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()