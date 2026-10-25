"""Validation for user-controlled identifiers and filenames."""

from __future__ import annotations

import re
from pathlib import PurePath
from uuid import UUID


class InputValidationError(ValueError):
    """Raised when an input fails application validation."""


_CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")
_SAFE_FILENAME = re.compile(r"^[^/\\]+$")


def validate_workspace_name(value: str) -> str:
    """Validate and normalize a workspace display name."""

    if not isinstance(value, str):
        raise InputValidationError("Workspace name must be text.")

    name = value.strip()

    if not name:
        raise InputValidationError("Workspace name is required.")

    if len(name) > 120:
        raise InputValidationError("Workspace name must be 120 characters or fewer.")

    if _CONTROL_CHARACTERS.search(name):
        raise InputValidationError("Workspace name contains unsupported characters.")

    return name


def validate_dataset_id(value: str) -> str:
    """Accept a canonical UUID dataset identifier."""

    if not isinstance(value, str):
        raise InputValidationError("Invalid dataset identifier.")

    try:
        parsed = UUID(value)
    except (ValueError, TypeError, AttributeError) as exc:
        raise InputValidationError("Invalid dataset identifier.") from exc

    return str(parsed)


def validate_filename(value: str) -> str:
    """Validate an uploaded filename without trusting its path."""

    if not isinstance(value, str):
        raise InputValidationError("Invalid filename.")

    # Reject control characters BEFORE stripping whitespace.
    # This ensures filenames such as "report.csv\n" are rejected.
    if _CONTROL_CHARACTERS.search(value):
        raise InputValidationError("Invalid filename.")

    filename = value.strip()

    if not filename or len(filename) > 255:
        raise InputValidationError("Invalid filename.")

    if not _SAFE_FILENAME.fullmatch(filename):
        raise InputValidationError("Invalid filename.")

    if filename in {".", ".."} or PurePath(filename).name != filename:
        raise InputValidationError("Invalid filename.")

    suffix = PurePath(filename).suffix.lower()

    if suffix not in {".csv", ".xlsx", ".xls"}:
        raise InputValidationError("Only CSV and Excel files are supported.")

    return filename
