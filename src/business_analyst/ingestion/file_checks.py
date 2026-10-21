
"""Pre-parse checks for untrusted tabular uploads."""

from __future__ import annotations

from io import BytesIO
from pathlib import PurePath
from zipfile import BadZipFile, ZipFile

from business_analyst.config import Settings
from business_analyst.exceptions import (
    FileSizeLimitError,
    IngestionConfigurationError,
    InvalidFileError,
    UnsupportedFileTypeError,
)

XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument."
    "spreadsheetml.sheet.main+xml"
)

XLSX_REQUIRED_MEMBERS = {
    "[Content_Types].xml",
    "xl/workbook.xml",
}


def normalize_filename(filename: str) -> str:
    """Return a safe display name without path components."""
    if not filename or not filename.strip():
        raise InvalidFileError("The uploaded file must have a filename.")

    # Handle Windows and POSIX separators regardless of host OS.
    normalized = filename.replace("\\", "/")
    name = PurePath(normalized).name

    if name in {"", ".", ".."}:
        raise InvalidFileError("The uploaded filename is invalid.")

    if any(ord(char) < 32 for char in name):
        raise InvalidFileError("The filename contains control characters.")

    return name


def detect_file_format(filename: str) -> str:
    """Determine supported format from the filename extension."""
    suffix = PurePath(filename).suffix.lower()

    if suffix == ".csv":
        return "csv"

    if suffix == ".xlsx":
        return "xlsx"

    if suffix == ".xls":
        raise UnsupportedFileTypeError(
            "Legacy .xls files are not supported. Save the workbook as .xlsx."
        )

    raise UnsupportedFileTypeError(
        "Unsupported file type. Upload a .csv or .xlsx file."
    )


def validate_file_size(data: bytes, settings: Settings) -> None:
    """Reject empty or oversized file payloads."""
    if not data:
        raise InvalidFileError("The uploaded file is empty.")

    if settings.max_upload_size_mb < 1:
        raise IngestionConfigurationError(
            "The configured upload limit must be at least 1 MB."
        )

    max_bytes = settings.max_upload_size_mb * 1024 * 1024

    if len(data) > max_bytes:
        raise FileSizeLimitError(
            f"File size exceeds the configured limit of "
            f"{settings.max_upload_size_mb} MB."
        )


def validate_csv_signature(data: bytes) -> None:
    """Reject obvious binary data and common format mismatches."""
    sample = data[:8192]

    if not sample:
        raise InvalidFileError("The CSV file contains no data.")

    if sample.startswith(b"PK\x03\x04"):
        raise InvalidFileError(
            "The content looks like an Excel workbook, not a CSV file."
        )

    if b"\x00" in sample:
        raise InvalidFileError(
            "The file contains binary data and cannot be parsed as CSV."
        )

    # CSV can be UTF-8, UTF-16, or another supported text encoding.
    # Do not require UTF-8 here; the CSV reader handles encoding candidates.


def validate_xlsx_signature(data: bytes) -> None:
    """Validate the basic XLSX archive structure and resource bounds."""
    if not data.startswith(b"PK\x03\x04"):
        raise InvalidFileError(
            "The file does not have a valid XLSX workbook signature."
        )

    try:
        with ZipFile(BytesIO(data)) as archive:
            infos = archive.infolist()
            names = {item.filename for item in infos}

            if not XLSX_REQUIRED_MEMBERS.issubset(names):
                raise InvalidFileError(
                    "The file is not a valid Excel XLSX workbook."
                )

            if len(infos) > 10_000:
                raise InvalidFileError(
                    "The workbook contains too many internal archive entries."
                )

            total_uncompressed = sum(item.file_size for item in infos)
            max_uncompressed = 200 * 1024 * 1024

            if total_uncompressed > max_uncompressed:
                raise InvalidFileError(
                    "The workbook expands beyond the permitted archive size."
                )

            for item in infos:
                if item.file_size > 0:
                    ratio = item.file_size / max(item.compress_size, 1)

                    if ratio > 200:
                        raise InvalidFileError(
                            "The workbook has a suspicious compression ratio."
                        )

    except BadZipFile as exc:
        raise InvalidFileError(
            "The Excel workbook archive is damaged or malformed."
        ) from exc
    except OSError as exc:
        raise InvalidFileError(
            "The Excel workbook could not be inspected."
        ) from exc
