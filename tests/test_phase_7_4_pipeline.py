"""Phase 7.4 integration tests for synthetic retail analysis and reporting."""

from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest

from business_analyst.analysis import AnalysisEngine
from business_analyst.reporting import ReportInputs, ReportingEngine


@pytest.fixture
def retail_data_with_invalid_records() -> pd.DataFrame:
    """Synthetic retail data containing missing and invalid values."""
    return pd.DataFrame(
        {
            "Order ID": ["O-100", "O-101", "O-102", "O-103", "O-103"],
            "Order Date": [
                "2026-01-01",
                "2026-01-02",
                "not-a-date",
                "2026-01-04",
                "2026-01-04",
            ],
            "Region": ["North", "South", "North", None, None],
            "Revenue": [100.0, 200.0, 150.0, None, None],
            "Profit": [20.0, 50.0, -10.0, 30.0, 30.0],
            "Quantity": [1, 2, 1, 1, 1],
        }
    )


@pytest.fixture
def cleaned_retail_data(
    retail_data_with_invalid_records: pd.DataFrame,
) -> pd.DataFrame:
    """Apply deterministic, reviewable cleaning to synthetic test data."""
    dataframe = retail_data_with_invalid_records.copy()

    dataframe["Order Date"] = pd.to_datetime(
        dataframe["Order Date"],
        errors="coerce",
    )

    for column in ("Revenue", "Profit", "Quantity"):
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

    # Drop rows missing required business identifiers or numeric metrics.
    dataframe = dataframe.dropna(
        subset=["Order ID", "Order Date", "Revenue", "Profit", "Quantity"]
    )

    # Remove exact duplicate records after normalizing values.
    dataframe = dataframe.drop_duplicates().reset_index(drop=True)

    # Fill missing categories with an explicit label rather than inventing
    # a real region for records that did not provide one.
    dataframe["Region"] = dataframe["Region"].fillna("Unknown")

    return dataframe


def test_synthetic_retail_data_contains_quality_issues(
    retail_data_with_invalid_records: pd.DataFrame,
) -> None:
    dataframe = retail_data_with_invalid_records

    assert dataframe["Revenue"].isna().any()
    assert dataframe["Region"].isna().any()
    assert (dataframe["Order Date"] == "not-a-date").any()
    assert dataframe.duplicated().any()


def test_cleaning_removes_invalid_rows_and_preserves_original(
    retail_data_with_invalid_records: pd.DataFrame,
    cleaned_retail_data: pd.DataFrame,
) -> None:
    original = retail_data_with_invalid_records

    # The original dataframe remains unchanged.
    assert original["Order Date"].dtype == object
    assert (original["Order Date"] == "not-a-date").any()

    # The cleaned copy has normalized types and no missing required fields.
    assert pd.api.types.is_datetime64_any_dtype(
        cleaned_retail_data["Order Date"]
    )
    assert not cleaned_retail_data[
        ["Order ID", "Order Date", "Revenue", "Profit", "Quantity"]
    ].isna().any().any()

    assert len(cleaned_retail_data) < len(original)


def test_analysis_engine_processes_cleaned_retail_data(
    retail_data_with_invalid_records: pd.DataFrame,
    cleaned_retail_data: pd.DataFrame,
) -> None:
    result = AnalysisEngine().run(
        cleaned_retail_data,
        dataset_id="phase-7-4-synthetic-retail",
        revenue_column="Revenue",
        profit_column="Profit",
        order_id_column="Order ID",
        quantity_column="Quantity",
        date_column="Order Date",
        trend_metric_column="Revenue",
        trend_frequency="M",
        group_column="Region",
        group_metric_column="Revenue",
        group_aggregation="sum",
        original_dataframe=retail_data_with_invalid_records,
        audit_trail=[
            {
                "operation": "normalize_dates",
                "column": "Order Date",
                "errors": "coerce",
            },
            {
                "operation": "drop_invalid_required_rows",
                "columns": [
                    "Order ID",
                    "Order Date",
                    "Revenue",
                    "Profit",
                    "Quantity",
                ],
            },
        ],
        quality_comparison=None,
    )

    assert result.row_count == len(cleaned_retail_data)
    assert result.column_count == len(cleaned_retail_data.columns)
    assert isinstance(result.kpis, list)


def test_reporting_engine_generates_pdf_and_excel(
    retail_data_with_invalid_records: pd.DataFrame,
    cleaned_retail_data: pd.DataFrame,
) -> None:
    analysis_result = AnalysisEngine().run(
        cleaned_retail_data,
        dataset_id="phase-7-4-report-test",
        revenue_column="Revenue",
        profit_column="Profit",
        order_id_column="Order ID",
        quantity_column="Quantity",
        date_column="Order Date",
        trend_metric_column="Revenue",
        trend_frequency="M",
        group_column="Region",
        group_metric_column="Revenue",
        group_aggregation="sum",
        original_dataframe=retail_data_with_invalid_records,
        audit_trail=[],
        quality_comparison=None,
    )

    inputs = ReportInputs(
        dataset_name="Synthetic Retail Integration Test",
        original_dataframe=retail_data_with_invalid_records,
        cleaned_dataframe=cleaned_retail_data,
        quality_report=None,
        quality_comparison=None,
        cleaning_audit=[],
        analysis_result=analysis_result,
        insight_report=None,
    )

    artifacts = ReportingEngine().generate(inputs)

    assert artifacts.pdf_bytes.startswith(b"%PDF")
    assert len(artifacts.pdf_bytes) > 100
    assert len(artifacts.excel_bytes) > 100
    assert artifacts.pdf_filename.lower().endswith(".pdf")
    assert artifacts.excel_filename.lower().endswith(".xlsx")


def test_synthetic_csv_can_be_read_by_pandas(
    cleaned_retail_data: pd.DataFrame,
) -> None:
    """Verify CSV serialization and re-ingestion for the demo data."""
    csv_bytes = cleaned_retail_data.to_csv(index=False).encode("utf-8")

    reloaded = pd.read_csv(BytesIO(csv_bytes), parse_dates=["Order Date"])

    assert len(reloaded) == len(cleaned_retail_data)
    assert list(reloaded.columns) == list(cleaned_retail_data.columns)