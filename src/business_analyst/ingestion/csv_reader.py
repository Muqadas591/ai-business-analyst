"""CSV parsing with bounded encoding and resource checks."""

from __future__ import annotations

import csv
from io import BytesIO, StringIO

import pandas as pd

from business_analyst.config import Settings
from business_analyst.exceptions import (
    ColumnLimitError,
    DuplicateHeaderError,
    EmptyDatasetError,
    EmptyFileError,
    InvalidFileError,
    MissingHeaderError,
    RowLimitError,
)
from business_analyst.ingestion.file_checks import validate_csv_signature

ENCODING_CANDIDATES = (
    "utf-8-sig",
    "utf-8",
    "cp1252",
    "latin-1",
)


def _decode_sample(data: bytes, sample_bytes: int) -> tuple[str, str]:
    """Decode a bounded sample using known text encodings."""
    sample = data[:sample_bytes]

    for encoding in ENCODING_CANDIDATES:
        try:
            return sample.decode(encoding), encoding
        except UnicodeDecodeError:
            continue

    raise InvalidFileError(
        "Could not decode the CSV file. Save it as UTF-8 and try again."
    )


def _detect_delimiter(sample: str) -> str:
    """Detect a common delimiter, falling back to a comma."""
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        return ","


def _validate_headers(columns: list[object], max_columns: int) -> list[str]:
    """Validate and normalize column labels without renaming duplicates."""
    if not columns or all(
        pd.isna(column) or not str(column).strip() for column in columns
    ):
        raise MissingHeaderError("The CSV file has no usable column headers.")

    if len(columns) > max_columns:
        raise ColumnLimitError(
            f"The file contains more than the allowed {max_columns} columns."
        )

    normalized = [str(column).strip() for column in columns]

    if any(not column for column in normalized):
        raise MissingHeaderError("One or more CSV column headers are empty.")

    if len(normalized) != len(set(normalized)):
        raise DuplicateHeaderError(
            "The CSV contains duplicate column headers. "
            "Rename them so every column has a unique name."
        )

    return normalized


def _read_original_headers(sample: str, delimiter: str) -> list[str]:
    """Read the original CSV header without pandas renaming duplicates."""
    try:
        reader = csv.reader(
            StringIO(sample, newline=""),
            delimiter=delimiter,
            strict=True,
        )
        return next(reader)
    except StopIteration as exc:
        raise EmptyFileError("The CSV file contains no header row.") from exc
    except csv.Error as exc:
        raise InvalidFileError(
            "The CSV header is malformed. Check its quoting and delimiter."
        ) from exc


def _validate_csv_syntax(data: bytes, encoding: str, delimiter: str) -> None:
    """Validate CSV quoting across the payload before pandas parses it."""
    try:
        text = data.decode(encoding)
        reader = csv.reader(
            StringIO(text, newline=""),
            delimiter=delimiter,
            strict=True,
        )
        for _ in reader:
            pass
    except (UnicodeDecodeError, csv.Error) as exc:
        raise InvalidFileError(
            "The CSV file contains malformed data or invalid text encoding."
        ) from exc


def read_csv_bytes(
    data: bytes,
    settings: Settings,
) -> tuple[pd.DataFrame, str, str]:
    """Parse CSV bytes and return (dataframe, encoding, delimiter)."""
    # Empty payload must be classified as EmptyFileError before signature
    # validation, which otherwise classifies it as an invalid file.
    if not data or not data.strip():
        raise EmptyFileError("The CSV file contains no readable content.")

    validate_csv_signature(data)

    sample, encoding = _decode_sample(data, settings.csv_sample_bytes)
    delimiter = _detect_delimiter(sample)

    # Check original headers before pandas can rename duplicate labels.
    original_headers = _read_original_headers(sample, delimiter)
    columns = _validate_headers(original_headers, settings.max_columns)

    if (
        "\n" not in sample
        and "\r" not in sample
        and len(data) > len(data[: settings.csv_sample_bytes])
    ):
        raise InvalidFileError("The CSV header is too long to inspect safely.")

    # Strict CSV parsing catches unterminated quotes that pandas may tolerate.
    _validate_csv_syntax(data, encoding, delimiter)

    try:
        dataframe = pd.read_csv(
            BytesIO(data),
            sep=delimiter,
            encoding=encoding,
            encoding_errors="strict",
            on_bad_lines="error",
            nrows=settings.max_rows + 1,
            low_memory=False,
        )
    except (pd.errors.ParserError, UnicodeError, ValueError, csv.Error) as exc:
        raise InvalidFileError(
            "The CSV could not be parsed. Check its encoding and row structure."
        ) from exc

    if len(dataframe) > settings.max_rows:
        raise RowLimitError(
            f"The CSV exceeds the configured limit of {settings.max_rows} data rows."
        )

    if dataframe.empty:
        raise EmptyDatasetError("The CSV contains headers but no data rows.")

    # Pandas may alter labels; compare against the original header validation.
    parsed_columns = [str(column).strip() for column in dataframe.columns]
    if parsed_columns != columns:
        raise InvalidFileError("The CSV header changed unexpectedly during parsing.")

    dataframe.columns = columns
    return dataframe, encoding, delimiter
