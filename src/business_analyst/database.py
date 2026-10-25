"""Database engine and SQLAlchemy session management."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from business_analyst.config import get_settings


settings = get_settings()

# Reuse one engine across Streamlit reruns.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
)

# Create short-lived sessions for individual database operations.
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


@contextmanager
def get_db_session() -> Iterator[Session]:
    """Provide a session and guarantee cleanup.

    The caller controls transaction boundaries by using session.commit().
    Exceptions trigger a rollback before the session is closed.
    """
    session = SessionLocal()

    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()