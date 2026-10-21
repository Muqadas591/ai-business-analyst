"""Typed result models for data-quality profiling and validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ColumnProfile:
    name: str
    inferred_type: str
    pandas_dtype: str
    row_count: int
    non_missing_count: int
    missing_count: int
    missing_fraction: float
    distinct_count: int
    sample_values: list[str] = field(default_factory=list)
    minimum: str | None = None
    maximum: str | None = None
    mean: float | None = None


@dataclass(frozen=True)
class QualityIssue:
    code: str
    severity: str
    category: str
    column: str | None
    message: str
    affected_rows: int
    row_numbers: list[int] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    recommendation: str = ""


@dataclass(frozen=True)
class QualityReport:
    row_count: int
    column_count: int
    duplicate_row_count: int
    profiles: list[ColumnProfile]
    issues: list[QualityIssue]
    schema_errors: list[str] = field(default_factory=list)

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    @property
    def error_count(self) -> int:
        return sum(issue.severity == "error" for issue in self.issues)

    @property
    def warning_count(self) -> int:
        return sum(issue.severity == "warning" for issue in self.issues)

    @property
    def affected_row_count(self) -> int:
        """Count distinct rows referenced by issues, not summed occurrences."""
        affected: set[int] = set()

        for issue in self.issues:
            affected.update(issue.row_numbers)

        return len(affected)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation of the report."""
        return asdict(self)
