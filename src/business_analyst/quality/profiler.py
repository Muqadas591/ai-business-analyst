"""Column statistics and lightweight data-type inference."""

from __future__ import annotations

import math

import pandas as pd

from business_analyst.quality.models import ColumnProfile


def _format_value(value: object) -> str:
    """Convert a sample or statistic to a readable string."""
    if pd.isna(value):
        return ""

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    return str(value)[:120]


def infer_column_type(series: pd.Series) -> str:
    """Infer a practical analytical type without changing the data."""
    non_missing = series.dropna()

    if non_missing.empty:
        return "empty"

    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    if pd.api.types.is_numeric_dtype(series):
        if pd.api.types.is_integer_dtype(series):
            return "integer"
        return "numeric"

    text = non_missing.astype("string").str.strip()
    non_empty = text[text.ne("")]

    if non_empty.empty:
        return "empty"

    numeric = pd.to_numeric(non_empty, errors="coerce")
    if numeric.notna().all():
        if (numeric % 1 == 0).all():
            return "integer-like"
        return "numeric-like"

    parsed_dates = pd.to_datetime(
        non_empty,
        errors="coerce",
        format="mixed",
    )
    if parsed_dates.notna().all():
        return "date-like"

    unique_count = non_empty.nunique()
    if unique_count <= max(20, int(len(non_empty) * 0.05)):
        return "categorical"

    return "text"


def profile_dataframe(
    dataframe: pd.DataFrame,
    sample_size: int = 5,
) -> list[ColumnProfile]:
    """Generate one profile per column without modifying the input."""
    profiles: list[ColumnProfile] = []
    row_count = len(dataframe)

    for column in dataframe.columns:
        series = dataframe[column]
        missing_mask = series.isna()

        # Treat whitespace-only strings as missing for quality profiling.
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            missing_mask = missing_mask | (
                series.astype("string").str.strip().eq("").fillna(False)
            )

        missing_count = int(missing_mask.sum())
        non_missing = series.loc[~missing_mask]
        distinct_count = int(non_missing.nunique())

        minimum: str | None = None
        maximum: str | None = None
        mean: float | None = None

        if not non_missing.empty:
            try:
                minimum = _format_value(non_missing.min())
                maximum = _format_value(non_missing.max())
            except (TypeError, ValueError):
                pass

            numeric = pd.to_numeric(non_missing, errors="coerce")
            valid_numeric = numeric.dropna()

            if len(valid_numeric) == len(non_missing):
                calculated_mean = float(valid_numeric.mean())
                if math.isfinite(calculated_mean):
                    mean = calculated_mean

        samples = [
            _format_value(value)
            for value in non_missing.drop_duplicates().head(sample_size)
        ]

        profiles.append(
            ColumnProfile(
                name=str(column),
                inferred_type=infer_column_type(series),
                pandas_dtype=str(series.dtype),
                row_count=row_count,
                non_missing_count=row_count - missing_count,
                missing_count=missing_count,
                missing_fraction=(missing_count / row_count if row_count else 0.0),
                distinct_count=distinct_count,
                sample_values=samples,
                minimum=minimum,
                maximum=maximum,
                mean=mean,
            )
        )

    return profiles
