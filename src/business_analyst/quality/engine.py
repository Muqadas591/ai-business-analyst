"""Orchestrate profiling, validation and explainable quality reporting."""

from __future__ import annotations

import pandas as pd

from business_analyst.quality.models import QualityIssue, QualityReport
from business_analyst.quality.profiler import profile_dataframe
from business_analyst.quality.rules import QualityRules
from business_analyst.quality.schemas import validate_with_pandera


def _row_numbers(mask: pd.Series) -> list[int]:
    """Return 1-based positional data row numbers for a Boolean mask."""
    return [
        position + 1
        for position, matched in enumerate(mask.fillna(False).tolist())
        if matched
    ]


def _is_missing(series: pd.Series) -> pd.Series:
    """Treat nulls and blank strings as missing."""
    missing = series.isna()

    if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
        missing = missing | (series.astype("string").str.strip().eq("").fillna(False))

    return missing


def _issue(
    *,
    code: str,
    severity: str,
    category: str,
    column: str | None,
    message: str,
    rows: list[int],
    examples: list[str] | None = None,
    recommendation: str = "",
) -> QualityIssue:
    return QualityIssue(
        code=code,
        severity=severity,
        category=category,
        column=column,
        message=message,
        affected_rows=len(rows),
        row_numbers=rows,
        examples=(examples or [])[:5],
        recommendation=recommendation,
    )


class DataQualityEngine:
    """Profile a DataFrame and evaluate configurable quality rules."""

    def __init__(self, rules: QualityRules | None = None) -> None:
        self.rules = rules or QualityRules()

    def run(self, dataframe: pd.DataFrame) -> QualityReport:
        """Run all quality checks and return a structured report."""
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("dataframe must be a pandas DataFrame.")

        # Preserve the original input; every check below is read-only.
        frame = dataframe.copy(deep=True)

        if frame.columns.duplicated().any():
            duplicate_names = (
                frame.columns[frame.columns.duplicated(keep=False)]
                .astype(str)
                .unique()
                .tolist()
            )
            duplicate_issue = _issue(
                code="DUPLICATE_COLUMN_NAMES",
                severity="error",
                category="schema",
                column=None,
                message="The dataset contains duplicate column names.",
                rows=[],
                examples=duplicate_names,
                recommendation=("Rename duplicate columns before further analysis."),
            )
            return QualityReport(
                row_count=len(frame),
                column_count=len(frame.columns),
                duplicate_row_count=0,
                profiles=[],
                issues=[duplicate_issue],
            )

        profiles = profile_dataframe(frame)
        issues: list[QualityIssue] = []

        # Column-name lookup is deliberately exact.
        available = set(frame.columns.astype(str))
        required = set(self.rules.required_columns)

        for column in sorted(required - available):
            issues.append(
                _issue(
                    code="MISSING_REQUIRED_COLUMN",
                    severity="error",
                    category="schema",
                    column=column,
                    message=f"Required column '{column}' is missing.",
                    rows=list(range(1, len(frame) + 1)),
                    recommendation=(
                        "Check the source file's headers or update the rules."
                    ),
                )
            )

        for column in frame.columns:
            name = str(column)
            missing_mask = _is_missing(frame[column])
            missing_count = int(missing_mask.sum())
            missing_rows = _row_numbers(missing_mask)

            if missing_count:
                is_required = name in required
                fraction = missing_count / len(frame) if len(frame) else 0.0
                exceeds_threshold = fraction > self.rules.max_missing_fraction

                if is_required or exceeds_threshold:
                    issues.append(
                        _issue(
                            code=(
                                "MISSING_REQUIRED_VALUE"
                                if is_required
                                else "MISSING_VALUE_THRESHOLD_EXCEEDED"
                            ),
                            severity="error" if is_required else "warning",
                            category="completeness",
                            column=name,
                            message=(
                                f"Column '{name}' has {missing_count} "
                                "missing or blank values."
                            ),
                            rows=missing_rows,
                            examples=(["<missing or blank>"]),
                            recommendation=(
                                "Review missing values and decide whether "
                                "to correct, retain, or exclude affected rows."
                            ),
                        )
                    )

        # Full-row duplicates. Only repeated occurrences after the first
        # are counted as duplicate rows.
        duplicate_mask = frame.duplicated(keep="first")
        duplicate_rows = _row_numbers(duplicate_mask)

        if duplicate_rows:
            issues.append(
                _issue(
                    code="DUPLICATE_ROWS",
                    severity=self.rules.duplicate_rows_severity,
                    category="uniqueness",
                    column=None,
                    message=(
                        f"{len(duplicate_rows)} rows duplicate an earlier "
                        "record across all columns."
                    ),
                    rows=duplicate_rows,
                    recommendation=(
                        "Inspect repeated records before deciding whether "
                        "they represent accidental duplicates."
                    ),
                )
            )

        # Duplicate business keys. Rows with missing key components are
        # excluded from duplicate-key matching and handled separately.
        key_columns = list(self.rules.key_columns)
        if key_columns and all(column in frame.columns for column in key_columns):
            key_frame = frame[key_columns]
            incomplete_key = key_frame.apply(_is_missing).any(axis=1)
            duplicate_key_mask = key_frame.duplicated(keep="first") & ~incomplete_key
            key_rows = _row_numbers(duplicate_key_mask)

            if key_rows:
                issues.append(
                    _issue(
                        code="DUPLICATE_KEY",
                        severity="error",
                        category="uniqueness",
                        column=", ".join(key_columns),
                        message=(
                            f"{len(key_rows)} rows repeat an earlier "
                            f"key using {key_columns}."
                        ),
                        rows=key_rows,
                        examples=[
                            str(value)
                            for value in key_frame.loc[duplicate_key_mask]
                            .head(5)
                            .to_dict(orient="records")
                        ],
                        recommendation=(
                            "Verify the intended unique key and resolve "
                            "duplicate business records."
                        ),
                    )
                )

        # Numeric conversion checks.
        for column in self.rules.numeric_columns:
            if column not in frame.columns:
                continue

            source = frame[column]
            missing_mask = _is_missing(source)
            converted = pd.to_numeric(source, errors="coerce")
            invalid_mask = converted.isna() & ~missing_mask
            invalid_rows = _row_numbers(invalid_mask)

            if invalid_rows:
                issues.append(
                    _issue(
                        code="INVALID_NUMERIC",
                        severity="error",
                        category="validity",
                        column=column,
                        message=(
                            f"{len(invalid_rows)} non-missing values in "
                            f"'{column}' cannot be converted to numbers."
                        ),
                        rows=invalid_rows,
                        examples=[
                            str(value)
                            for value in source.loc[invalid_mask]
                            .drop_duplicates()
                            .head(5)
                        ],
                        recommendation=(
                            "Review the source values, decimal separators, "
                            "currency symbols and unexpected text."
                        ),
                    )
                )

        # Date conversion checks.
        for column in self.rules.date_columns:
            if column not in frame.columns:
                continue

            source = frame[column]
            missing_mask = _is_missing(source)
            date_format = self.rules.date_formats.get(column)

            try:
                converted = pd.to_datetime(
                    source,
                    errors="coerce",
                    format=date_format or "mixed",
                )
            except (ValueError, TypeError):
                converted = pd.to_datetime(
                    source,
                    errors="coerce",
                )

            invalid_mask = converted.isna() & ~missing_mask
            invalid_rows = _row_numbers(invalid_mask)

            if invalid_rows:
                issues.append(
                    _issue(
                        code="INVALID_DATE",
                        severity="error",
                        category="validity",
                        column=column,
                        message=(
                            f"{len(invalid_rows)} non-missing values in "
                            f"'{column}' are not valid dates."
                        ),
                        rows=invalid_rows,
                        examples=[
                            str(value)
                            for value in source.loc[invalid_mask]
                            .drop_duplicates()
                            .head(5)
                        ],
                        recommendation=(
                            "Confirm the expected date format and correct "
                            "invalid or ambiguous date values."
                        ),
                    )
                )

        # Inconsistent category spellings: whitespace/case variants only.
        for column in self.rules.category_columns:
            if column not in frame.columns:
                continue

            source = frame[column]
            missing_mask = _is_missing(source)
            normalized = source.astype("string").str.strip().str.casefold()

            variants: dict[str, set[str]] = {}
            for value in source.loc[~missing_mask].astype(str):
                key = value.strip().casefold()
                variants.setdefault(key, set()).add(value)

            inconsistent_keys = {
                key for key, values in variants.items() if len(values) > 1
            }

            inconsistent_mask = normalized.isin(inconsistent_keys) & ~missing_mask
            inconsistent_rows = _row_numbers(inconsistent_mask)

            if inconsistent_rows:
                examples = [
                    ", ".join(sorted(variants[key]))
                    for key in sorted(inconsistent_keys)[:5]
                ]
                issues.append(
                    _issue(
                        code="INCONSISTENT_CATEGORY",
                        severity="warning",
                        category="consistency",
                        column=column,
                        message=(
                            f"Column '{column}' has category values that "
                            "differ only by case or surrounding whitespace."
                        ),
                        rows=inconsistent_rows,
                        examples=examples,
                        recommendation=(
                            "Review category spelling and capitalization "
                            "before standardizing labels."
                        ),
                    )
                )

        # Exact allowed-value checks are separate from spelling variants.
        for column, allowed in self.rules.allowed_categories.items():
            if column not in frame.columns:
                continue

            source = frame[column]
            missing_mask = _is_missing(source)
            allowed_set = set(allowed)
            invalid_mask = (
                ~source.astype("string").str.strip().isin(allowed_set) & ~missing_mask
            )
            invalid_rows = _row_numbers(invalid_mask)

            if invalid_rows:
                issues.append(
                    _issue(
                        code="UNEXPECTED_CATEGORY",
                        severity="error",
                        category="validity",
                        column=column,
                        message=(
                            f"{len(invalid_rows)} values in '{column}' "
                            "are outside the allowed category list."
                        ),
                        rows=invalid_rows,
                        examples=[
                            str(value)
                            for value in source.loc[invalid_mask]
                            .drop_duplicates()
                            .head(5)
                        ],
                        recommendation=(
                            "Confirm the allowed values with the business "
                            "owner; do not automatically discard new values."
                        ),
                    )
                )

        schema_errors = validate_with_pandera(frame, self.rules)

        return QualityReport(
            row_count=len(frame),
            column_count=len(frame.columns),
            duplicate_row_count=len(duplicate_rows),
            profiles=profiles,
            issues=issues,
            schema_errors=schema_errors,
        )
