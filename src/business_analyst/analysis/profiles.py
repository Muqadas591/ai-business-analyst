"""Numeric and categorical distributions."""

from __future__ import annotations

from typing import Any

import pandas as pd


def numeric_profiles(
    dataframe: pd.DataFrame,
) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}

    for column in dataframe.select_dtypes(include="number").columns:
        series = dataframe[column]
        valid = series.dropna()

        profiles[column] = {
            "count": int(valid.count()),
            "missing_count": int(series.isna().sum()),
            "mean": float(valid.mean()) if not valid.empty else None,
            "median": float(valid.median()) if not valid.empty else None,
            "std": float(valid.std()) if len(valid) > 1 else None,
            "min": float(valid.min()) if not valid.empty else None,
            "q25": float(valid.quantile(0.25)) if not valid.empty else None,
            "q75": float(valid.quantile(0.75)) if not valid.empty else None,
            "max": float(valid.max()) if not valid.empty else None,
            "sum": float(valid.sum()) if not valid.empty else None,
        }

    return profiles


def categorical_profiles(
    dataframe: pd.DataFrame,
    top_n: int = 20,
) -> dict[str, list[dict[str, Any]]]:
    if top_n < 1:
        raise ValueError("top_n must be at least 1.")

    profiles: dict[str, list[dict[str, Any]]] = {}

    for column in dataframe.select_dtypes(
        include=["object", "category", "bool", "string"]
    ).columns:
        counts = (
            dataframe[column]
            .astype("string")
            .fillna("<MISSING>")
            .value_counts(dropna=False)
            .head(top_n)
        )

        profiles[column] = [
            {
                "category": str(category),
                "count": int(count),
                "percentage": round(float(count / len(dataframe) * 100), 2)
                if len(dataframe)
                else 0.0,
            }
            for category, count in counts.items()
        ]

    return profiles
