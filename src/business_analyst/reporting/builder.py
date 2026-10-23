from __future__ import annotations

import json
import math
from typing import Any

import pandas as pd

from business_analyst.reporting.models import ReportInputs


def _serialize(value: Any) -> Any:
    """Convert common Python, pandas, and Pydantic values to safe data."""
    if hasattr(value, "model_dump"):
        return _serialize(value.model_dump(mode="json"))

    if hasattr(value, "to_dict") and not isinstance(value, pd.DataFrame):
        try:
            return _serialize(value.to_dict())
        except (TypeError, ValueError):
            pass

    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]

    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")

    if isinstance(value, pd.Series):
        return value.tolist()

    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()

    if value is None or isinstance(value, (str, int, bool)):
        return value

    if isinstance(value, float):
        return value if math.isfinite(value) else None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    return str(value)


def _as_dict(value: Any) -> dict[str, Any]:
    result = _serialize(value)
    return result if isinstance(result, dict) else {}


def _quality_summary(
    original: pd.DataFrame,
    cleaned: pd.DataFrame,
    quality_report: Any | None,
    comparison: Any | None,
) -> dict[str, Any]:
    before_missing = int(original.isna().sum().sum())
    after_missing = int(cleaned.isna().sum().sum())

    before_duplicates = int(original.duplicated().sum())
    after_duplicates = int(cleaned.duplicated().sum())

    return {
        "before": {
            "rows": int(len(original)),
            "columns": int(len(original.columns)),
            "missing_cells": before_missing,
            "duplicate_rows": before_duplicates,
        },
        "after": {
            "rows": int(len(cleaned)),
            "columns": int(len(cleaned.columns)),
            "missing_cells": after_missing,
            "duplicate_rows": after_duplicates,
        },
        "quality_report": _as_dict(quality_report),
        "comparison": _as_dict(comparison),
    }


def _cleaning_summary(audit: list[dict[str, Any]] | None) -> dict[str, Any]:
    entries = _serialize(audit or [])
    if not isinstance(entries, list):
        entries = []

    return {
        "operation_count": len(entries),
        "audit_trail": entries,
    }


def _limitations(
    analysis: dict[str, Any],
    insights: dict[str, Any],
) -> list[str]:
    limitations: list[str] = [
        "Findings describe the supplied dataset and do not establish causation.",
        "Data-quality statistics describe the data available at report generation time.",
        "AI-generated recommendations require review by a qualified business owner.",
    ]

    for finding in analysis.get("findings", []) or []:
        if isinstance(finding, dict):
            for item in finding.get("limitations", []) or []:
                if isinstance(item, str) and item not in limitations:
                    limitations.append(item)

    for item in insights.get("overall_limitations", []) or []:
        if isinstance(item, str) and item not in limitations:
            limitations.append(item)

    if not insights:
        limitations.append(
            "AI recommendations were not included because no insight report "
            "was supplied."
        )

    return limitations


def build_report_data(inputs: ReportInputs) -> dict[str, Any]:
    """Create the shared payload used by both export formats."""
    original = inputs.original_dataframe
    cleaned = inputs.cleaned_dataframe

    analysis = _as_dict(inputs.analysis_result)
    insights = _as_dict(inputs.insight_report)

    columns = []
    for name in cleaned.columns:
        series = cleaned[name]
        columns.append(
            {
                "name": str(name),
                "dtype": str(series.dtype),
                "missing_count": int(series.isna().sum()),
                "distinct_count": int(series.nunique(dropna=True)),
            }
        )

    return {
        "report_version": "1.0",
        "dataset": {
            "name": inputs.dataset_name,
            "original_rows": int(len(original)),
            "cleaned_rows": int(len(cleaned)),
            "original_columns": int(len(original.columns)),
            "cleaned_columns": int(len(cleaned.columns)),
            "columns": columns,
        },
        "quality": _quality_summary(
            original,
            cleaned,
            inputs.quality_report,
            inputs.quality_comparison,
        ),
        "cleaning": _cleaning_summary(inputs.cleaning_audit),
        "analysis": analysis,
        "insights": insights,
        "limitations": _limitations(analysis, insights),
        "lineage": _serialize(analysis.get("lineage", {})),
    }
