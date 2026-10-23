from __future__ import annotations

from typing import Any


def _records(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]

    if isinstance(value, dict):
        # Support serialized table-like structures.
        for key in ("records", "data", "items", "values"):
            nested = value.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]

    return []


def _first_present(record: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in record and record[key] is not None:
            return record[key]
    return None


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        number = float(value)
        if number == number and abs(number) != float("inf"):
            return number

    return None


def build_chart_specs(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    """Build chart specifications from serialized Phase 4 results."""
    charts: list[dict[str, Any]] = []

    trends = analysis.get("trends", [])
    trend_records = _records(trends)

    trend_points = []
    for record in trend_records:
        label = _first_present(record, ("period", "date", "label", "x", "name"))
        value = _numeric(
            _first_present(record, ("value", "total", "sum", "y", "metric"))
        )
        if label is not None and value is not None:
            trend_points.append({"label": str(label), "value": value})

    if trend_points:
        charts.append(
            {
                "title": "Trend over time",
                "kind": "line",
                "points": trend_points[:100],
            }
        )

    grouped = analysis.get("grouped_summaries", [])
    group_records = _records(grouped)

    group_points = []
    for record in group_records:
        label = _first_present(record, ("group", "category", "label", "name", "key"))
        value = _numeric(
            _first_present(record, ("value", "sum", "mean", "median", "count"))
        )
        if label is not None and value is not None:
            group_points.append({"label": str(label), "value": value})

    if group_points:
        charts.append(
            {
                "title": "Comparison by group",
                "kind": "bar",
                "points": sorted(
                    group_points, key=lambda point: abs(point["value"]), reverse=True
                )[:15],
            }
        )

    return charts
