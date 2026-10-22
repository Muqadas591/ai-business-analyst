"""Compare data quality before and after cleaning."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from business_analyst.quality import DataQualityEngine, QualityRules


@dataclass(frozen=True)
class QualityComparison:
    rows_before: int
    rows_after: int
    columns_before: int
    columns_after: int
    issues_before: int
    issues_after: int
    errors_before: int
    errors_after: int
    warnings_before: int
    warnings_after: int
    missing_cells_before: int
    missing_cells_after: int
    duplicate_rows_before: int
    duplicate_rows_after: int
    issue_count_change: int


def compare_quality(
    original: pd.DataFrame,
    cleaned: pd.DataFrame,
    rules: QualityRules | None = None,
) -> QualityComparison:
    """Profile both datasets and summarize quality changes."""
    engine = DataQualityEngine(rules)
    before = engine.run(original)
    after = engine.run(cleaned)

    return QualityComparison(
        rows_before=before.row_count,
        rows_after=after.row_count,
        columns_before=before.column_count,
        columns_after=after.column_count,
        issues_before=before.issue_count,
        issues_after=after.issue_count,
        errors_before=before.error_count,
        errors_after=after.error_count,
        warnings_before=before.warning_count,
        warnings_after=after.warning_count,
        missing_cells_before=sum(profile.missing_count for profile in before.profiles),
        missing_cells_after=sum(profile.missing_count for profile in after.profiles),
        duplicate_rows_before=before.duplicate_row_count,
        duplicate_rows_after=after.duplicate_row_count,
        issue_count_change=after.issue_count - before.issue_count,
    )
