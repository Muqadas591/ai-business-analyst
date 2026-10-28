"""Database engine and SQLAlchemy session management."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from business_analyst.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


def create_database_engine() -> Engine:
    """Create the application database engine.

    PostgreSQL connections use a bounded connection pool and a connection
    timeout. SQLite receives compatible connection arguments without
    PostgreSQL-specific pool settings.
    """
    database_url = settings.database_url
    is_sqlite = database_url.lower().startswith("sqlite:")

    engine_options: dict = {
        "pool_pre_ping": True,
    }

    if is_sqlite:
        engine_options["connect_args"] = {
            "check_same_thread": False,
        }
    else:
        engine_options.update(
            {
                "pool_size": settings.db_pool_size,
                "max_overflow": settings.db_max_overflow,
                "pool_timeout": settings.db_pool_timeout_seconds,
                "pool_recycle": settings.db_pool_recycle_seconds,
                "connect_args": {
                    "connect_timeout": settings.db_connect_timeout_seconds,
                },
            }
        )

    return create_engine(database_url, **engine_options)


# Reuse one engine across Streamlit reruns.
engine = create_database_engine()

# Create short-lived sessions for individual database operations.
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


@contextmanager
def get_db_session() -> Iterator[Session]:
    """Provide a database session and guarantee cleanup.

    The caller controls transaction boundaries by calling session.commit().
    If an exception occurs, the transaction is rolled back before the
    session is closed.
    """
    session = SessionLocal()

    try:
        yield session
    except Exception:
        try:
            session.rollback()
        except SQLAlchemyError:
            logger.exception("Database rollback failed.")
        raise
    finally:
        session.close()


def check_database_connection() -> bool:
    """Return whether the configured database can execute a simple query.

    This function does not expose database credentials or connection details
    in its return value. Failure details are recorded in application logs.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True

    except SQLAlchemyError:
        logger.exception("Database connectivity check failed.")
        return False