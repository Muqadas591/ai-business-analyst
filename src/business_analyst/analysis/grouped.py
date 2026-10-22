"""Grouped business summaries and rankings."""

from __future__ import annotations

import pandas as pd


def grouped_summary(
    dataframe: pd.DataFrame,
    group_column: str,
    metric_column: str,
    aggregation: str = "sum",
    top_n: int = 20,
) -> list[dict[str, object]]:
    if group_column not in dataframe.columns:
        raise ValueError(f"Unknown group column: {group_column}")

    if metric_column not in dataframe.columns:
        raise ValueError(f"Unknown metric column: {metric_column}")

    if not pd.api.types.is_numeric_dtype(dataframe[metric_column]):
        raise ValueError(f"{metric_column} must be numeric.")

    if aggregation not in {"sum", "mean", "median", "count"}:
        raise ValueError("Unsupported aggregation.")

    if top_n < 1:
        raise ValueError("top_n must be at least 1.")

    work = dataframe[[group_column, metric_column]].copy()
    work[group_column] = work[group_column].astype("string").fillna("<MISSING>")

    grouped = work.groupby(group_column, dropna=False, observed=True)[metric_column]

    if aggregation == "sum":
        result = grouped.sum(min_count=1)
    elif aggregation == "mean":
        result = grouped.mean()
    elif aggregation == "median":
        result = grouped.median()
    else:
        result = grouped.count()

    result = result.dropna().sort_values(ascending=False).head(top_n)

    return [
        {
            "group": str(group),
            "value": float(value),
            "aggregation": aggregation,
        }
        for group, value in result.items()
    ]
