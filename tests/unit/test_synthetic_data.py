"""Tests for the synthetic retail data generator."""

import pandas as pd
import pytest

from business_analyst.synthetic_data import (
    generate_retail_sales,
    retail_sales_csv_bytes,
    retail_sales_excel_bytes,
)


def test_generator_returns_expected_columns() -> None:
    dataframe = generate_retail_sales(rows=10)

    assert len(dataframe) == 10
    assert {
        "order_id",
        "order_date",
        "region",
        "product",
        "quantity",
        "revenue",
        "cost",
        "profit",
    }.issubset(dataframe.columns)


def test_generator_is_reproducible() -> None:
    first = generate_retail_sales(rows=20, seed=123)
    second = generate_retail_sales(rows=20, seed=123)

    pd.testing.assert_frame_equal(first, second)


def test_generator_rejects_zero_rows() -> None:
    with pytest.raises(ValueError):
        generate_retail_sales(rows=0)


def test_csv_export_is_readable() -> None:
    dataframe = pd.read_csv(__import__("io").BytesIO(retail_sales_csv_bytes(rows=5)))

    assert len(dataframe) == 5


def test_excel_export_contains_multiple_sheets() -> None:
    from business_analyst.ingestion.excel_reader import list_excel_sheets

    workbook_bytes = retail_sales_excel_bytes(rows=10)

    assert list_excel_sheets(workbook_bytes) == ["Sales", "Preview"]
