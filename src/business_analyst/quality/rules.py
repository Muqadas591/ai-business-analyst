"""Configuration for reusable data-quality checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["error", "warning"]


@dataclass(frozen=True)
class QualityRules:
    """User-configurable rules applied to an input DataFrame."""

    required_columns: tuple[str, ...] = ()
    key_columns: tuple[str, ...] = ()
    numeric_columns: tuple[str, ...] = ()
    date_columns: tuple[str, ...] = ()

    # Optional exact allowed values for categorical columns.
    allowed_categories: dict[str, tuple[str, ...]] = field(default_factory=dict)

    # Optional date parsing formats, keyed by column name.
    date_formats: dict[str, str] = field(default_factory=dict)

    # Columns where case/whitespace variants should be reported.
    category_columns: tuple[str, ...] = ()

    # Missing-value thresholds are fractions from 0.0 to 1.0.
    max_missing_fraction: float = 0.0

    # Rows duplicated across every column are reported as warnings by default.
    duplicate_rows_severity: Severity = "warning"

    def __post_init__(self) -> None:
        if not 0.0 <= self.max_missing_fraction <= 1.0:
            raise ValueError("max_missing_fraction must be between 0.0 and 1.0.")

        if self.duplicate_rows_severity not in ("error", "warning"):
            raise ValueError("duplicate_rows_severity must be 'error' or 'warning'.")

        for column, values in self.allowed_categories.items():
            if not values:
                raise ValueError(f"Allowed categories for '{column}' cannot be empty.")
