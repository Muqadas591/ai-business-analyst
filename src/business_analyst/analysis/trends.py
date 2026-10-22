"""Time-series aggregation and period-over-period changes."""

from __future__ import annotations

import pandas as pd


def calculate_trend(
    dataframe: pd.DataFrame,
    date_column: str,
    metric_column: str,
    frequency: str = "M",
) -> list[dict[str, object]]:
    if date_column not in dataframe.columns:
        raise ValueError(f"Unknown date column: {date_column}")

    if metric_column not in dataframe.columns:
        raise ValueError(f"Unknown metric column: {metric_column}")

    if not pd.api.types.is_numeric_dtype(dataframe[metric_column]):
        raise ValueError(f"{metric_column} must be numeric.")

    allowed_frequencies = {"D", "W", "M", "Q", "Y"}
    if frequency not in allowed_frequencies:
        raise ValueError(
            f"Unsupported frequency {frequency!r}. "
            f"Choose one of {sorted(allowed_frequencies)}."
        )

    dates = pd.to_datetime(dataframe[date_column], errors="coerce")
    values = dataframe[metric_column]

    valid = pd.DataFrame({"date": dates, "value": values})
    valid = valid.dropna(subset=["date", "value"])

    if valid.empty:
        return []

    # Use period labels so results are stable and easy to display.
    period_frequency = {
        "D": "D",
        "W": "W-SUN",
        "M": "M",
        "Q": "Q",
        "Y": "Y",
    }[frequency]

    valid["period"] = valid["date"].dt.to_period(period_frequency)

    grouped = valid.groupby("period", observed=True)["value"].sum().sort_index()

    output: list[dict[str, object]] = []
    previous: float | None = None

    for period, value in grouped.items():
        current = float(value)
        change = current - previous if previous is not None else None
        change_pct = (
            (change / abs(previous)) * 100
            if change is not None and previous not in (None, 0)
            else None
        )

        output.append(
            {
                "period": str(period),
                "value": current,
                "previous_value": previous,
                "change": change,
                "change_pct": change_pct,
            }
        )
        previous = current

    return output
