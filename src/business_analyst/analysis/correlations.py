"""Numeric correlation analysis."""

from __future__ import annotations

import pandas as pd


def calculate_correlations(
    dataframe: pd.DataFrame,
    min_periods: int = 3,
) -> list[dict[str, object]]:
    if min_periods < 2:
        raise ValueError("min_periods must be at least 2.")

    numeric = dataframe.select_dtypes(include="number")
    if numeric.shape[1] < 2:
        return []

    matrix = numeric.corr(method="pearson", min_periods=min_periods)
    results: list[dict[str, object]] = []

    for i, left in enumerate(matrix.columns):
        for right in matrix.columns[i + 1 :]:
            value = matrix.loc[left, right]
            if pd.isna(value):
                continue

            coefficient = float(value)
            strength = (
                "strong"
                if abs(coefficient) >= 0.7
                else "moderate"
                if abs(coefficient) >= 0.4
                else "weak"
            )

            results.append(
                {
                    "column_a": str(left),
                    "column_b": str(right),
                    "correlation": coefficient,
                    "strength": strength,
                    "direction": (
                        "positive"
                        if coefficient > 0
                        else "negative"
                        if coefficient < 0
                        else "none"
                    ),
                    "interpretation": (
                        "Association only; this result does not establish causation."
                    ),
                }
            )

    return sorted(
        results,
        key=lambda item: abs(float(item["correlation"])),
        reverse=True,
    )
