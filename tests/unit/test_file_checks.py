"""Tests for upload checks."""

import pytest

from business_analyst.exceptions import (
    FileSizeLimitError,
    InvalidFileError,
    UnsupportedFileTypeError,
)
from business_analyst.ingestion.file_checks import (
    detect_file_format,
    normalize_filename,
    validate_csv_signature,
    validate_file_size,
    validate_xlsx_signature,
)


def test_filename_normalization_removes_path() -> None:
    assert normalize_filename(r"C:\fakepath\sales.csv") == "sales.csv"


def test_rejects_empty_filename() -> None:
    with pytest.raises(InvalidFileError):
        normalize_filename(" ")


def test_csv_extension_is_case_insensitive() -> None:
    assert detect_file_format("SALES.CSV") == "csv"


def test_rejects_legacy_excel() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        detect_file_format("sales.xls")


def test_rejects_unknown_extension() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        detect_file_format("sales.exe")


def test_rejects_empty_payload(test_settings) -> None:
    with pytest.raises(InvalidFileError):
        validate_file_size(b"", test_settings)


def test_rejects_oversized_payload(test_settings) -> None:
    payload = b"x" * (1024 * 1024 + 1)

    with pytest.raises(FileSizeLimitError):
        validate_file_size(payload, test_settings)


def test_rejects_binary_csv() -> None:
    with pytest.raises(InvalidFileError):
        validate_csv_signature(b"header\x00value")


def test_rejects_fake_xlsx() -> None:
    with pytest.raises(InvalidFileError):
        validate_xlsx_signature(b"PK\x03\x04not-a-real-workbook")
