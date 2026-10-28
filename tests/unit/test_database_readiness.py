"""Tests for database engine configuration and readiness checks."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import SingletonThreadPool

from business_analyst import database


def test_sqlite_engine_uses_compatible_connection_options(monkeypatch):
    """SQLite engines should not receive PostgreSQL-only pool options."""
    monkeypatch.setattr(
        database,
        "settings",
        SimpleNamespace(database_url="sqlite://"),
    )

    engine = database.create_database_engine()

    try:
        assert isinstance(engine.pool, SingletonThreadPool)

        with engine.connect() as connection:
            result = connection.exec_driver_sql("SELECT 1").scalar_one()

        assert result == 1
    finally:
        engine.dispose()


def test_database_connection_check_succeeds(monkeypatch):
    """A successful SELECT 1 should return True."""
    fake_engine = MagicMock()
    fake_connection = fake_engine.connect.return_value.__enter__.return_value

    monkeypatch.setattr(database, "engine", fake_engine)

    assert database.check_database_connection() is True

    fake_connection.execute.assert_called_once()


def test_database_connection_check_handles_database_error(monkeypatch):
    """A SQLAlchemy connection error should return False."""
    fake_engine = MagicMock()
    fake_engine.connect.side_effect = SQLAlchemyError("database unavailable")

    monkeypatch.setattr(database, "engine", fake_engine)

    assert database.check_database_connection() is False