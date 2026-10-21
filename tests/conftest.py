
"""Shared pytest fixtures."""

from io import BytesIO

import pandas as pd
import pytest
from openpyxl import Workbook

from business_analyst.config import Settings


@pytest.fixture
def test_settings() -> Settings:
    """Return small, isolated settings for ingestion tests."""
    return Settings(
        _env_file=None,
        app_env="test",
        app_debug=False,
        database_url="sqlite:///:memory:",
        auth_secret_key="test-only-secret-not-for-production",
        ai_provider="disabled",
        max_upload_size_mb=1,
        max_rows=5,
        max_columns=5,
        csv_sample_bytes=1024,
    )


@pytest.fixture
def csv_bytes() -> bytes:
    """Return a small, valid UTF-8 CSV dataset."""
    return (
        b"order_id,region,revenue\n"
        b"ORD-001,North,100.0\n"
        b"ORD-002,South,200.0\n"
    )


@pytest.fixture
def xlsx_bytes() -> bytes:
    """Return an XLSX workbook with two worksheets."""
    workbook = Workbook()
    sales = workbook.active
    sales.title = "Sales"
    sales.append(["order_id", "revenue"])
    sales.append(["ORD-001", 100])
    sales.append(["ORD-002", 200])

    preview = workbook.create_sheet("Preview")
    preview.append(["category", "count"])
    preview.append(["A", 2])

    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()
    return buffer.getvalue()


@pytest.fixture
def dataframe() -> pd.DataFrame:
    """Return a tiny known-answer DataFrame."""
    return pd.DataFrame(
        {
            "region": ["North", "South"],
            "revenue": [100.0, 200.0],
        }
    )
