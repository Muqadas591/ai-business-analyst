"""Tests for the public ingestion service."""

import pytest

from business_analyst.exceptions import (
    IngestionConfigurationError,
    SheetSelectionError,
    UnsupportedFileTypeError,
)
from business_analyst.ingestion import DataIngestionService


def test_ingests_csv(csv_bytes, test_settings) -> None:
    service = DataIngestionService(test_settings)

    result = service.ingest("sales.csv", csv_bytes)

    assert result.row_count == 2
    assert result.column_count == 3
    assert result.source.file_format == "csv"
    assert result.source.sheet_name is None
    assert result.source.file_size_bytes == len(csv_bytes)


def test_requires_explicit_sheet_for_multi_sheet_excel(
    xlsx_bytes,
    test_settings,
) -> None:
    service = DataIngestionService(test_settings)

    with pytest.raises(IngestionConfigurationError):
        service.ingest("sales.xlsx", xlsx_bytes)


def test_ingests_selected_excel_sheet(xlsx_bytes, test_settings) -> None:
    service = DataIngestionService(test_settings)

    result = service.ingest(
        "sales.xlsx",
        xlsx_bytes,
        sheet_name="Sales",
    )

    assert result.row_count == 2
    assert result.column_count == 2
    assert result.source.sheet_name == "Sales"
    assert result.source.file_format == "xlsx"


def test_lists_sheets_for_excel(xlsx_bytes, test_settings) -> None:
    service = DataIngestionService(test_settings)

    assert service.list_sheets("sales.xlsx", xlsx_bytes) == [
        "Sales",
        "Preview",
    ]


def test_rejects_sheet_selection_for_csv(
    csv_bytes,
    test_settings,
) -> None:
    service = DataIngestionService(test_settings)

    with pytest.raises(IngestionConfigurationError):
        service.ingest(
            "sales.csv",
            csv_bytes,
            sheet_name="Sales",
        )


def test_rejects_unsupported_file(csv_bytes, test_settings) -> None:
    service = DataIngestionService(test_settings)

    with pytest.raises(UnsupportedFileTypeError):
        service.ingest("sales.json", csv_bytes)


def test_rejects_nonexistent_sheet(xlsx_bytes, test_settings) -> None:
    service = DataIngestionService(test_settings)

    with pytest.raises(SheetSelectionError):
        service.ingest(
            "sales.xlsx",
            xlsx_bytes,
            sheet_name="Missing",
        )
