"""Orchestrate EDA, KPI calculations, findings, and lineage."""

from __future__ import annotations

from typing import Any

import pandas as pd

from business_analyst.analysis.correlations import calculate_correlations
from business_analyst.analysis.findings import generate_findings
from business_analyst.analysis.grouped import grouped_summary
from business_analyst.analysis.kpis import calculate_kpis
from business_analyst.analysis.lineage import build_lineage
from business_analyst.analysis.models import AnalysisResult
from business_analyst.analysis.profiles import (
    categorical_profiles,
    numeric_profiles,
)
from business_analyst.analysis.trends import calculate_trend


class AnalysisEngine:
    """Run reproducible descriptive analytics on a cleaned dataset."""

    def run(
        self,
        dataframe: pd.DataFrame,
        *,
        dataset_id: str = "dataset",
        revenue_column: str | None = None,
        profit_column: str | None = None,
        order_id_column: str | None = None,
        quantity_column: str | None = None,
        date_column: str | None = None,
        trend_metric_column: str | None = None,
        trend_frequency: str = "M",
        group_column: str | None = None,
        group_metric_column: str | None = None,
        group_aggregation: str = "sum",
        original_dataframe: pd.DataFrame | None = None,
        audit_trail: list[dict[str, Any]] | None = None,
        quality_comparison: dict[str, Any] | None = None,
    ) -> AnalysisResult:
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("dataframe must be a pandas DataFrame.")

        if dataframe.empty:
            raise ValueError(
                "The cleaned dataset is empty. Upload or prepare "
                "a dataset with at least one row before analysis."
            )

        if len(dataframe.columns) == 0:
            raise ValueError("The dataset must contain at least one column.")

        # Snapshot the data so analysis cannot modify the caller's DataFrame.
        analyzed = dataframe.copy(deep=True)
        original = (
            original_dataframe.copy(deep=True)
            if original_dataframe is not None
            else analyzed.copy(deep=True)
        )

        kpis = calculate_kpis(
            analyzed,
            revenue_column=revenue_column,
            profit_column=profit_column,
            order_id_column=order_id_column,
            quantity_column=quantity_column,
        )

        trends: dict[str, list[dict[str, object]]] = {}
        if date_column and trend_metric_column:
            key = f"{trend_metric_column}_by_{date_column}"
            trends[key] = calculate_trend(
                analyzed,
                date_column,
                trend_metric_column,
                trend_frequency,
            )

        correlations = calculate_correlations(analyzed)

        grouped: dict[str, list[dict[str, object]]] = {}
        if group_column and group_metric_column:
            key = f"{group_metric_column}_by_{group_column}_{group_aggregation}"
            grouped[key] = grouped_summary(
                analyzed,
                group_column,
                group_metric_column,
                group_aggregation,
            )

        findings = generate_findings(kpis, grouped, trends, correlations)

        lineage = build_lineage(
            original,
            analyzed,
            audit_trail=audit_trail,
            quality_comparison=quality_comparison,
        )

        return AnalysisResult(
            dataset_id=dataset_id,
            row_count=len(analyzed),
            column_count=len(analyzed.columns),
            numeric_profiles=numeric_profiles(analyzed),
            categorical_profiles=categorical_profiles(analyzed),
            trends=trends,
            correlations=correlations,
            grouped_summaries=grouped,
            kpis=kpis,
            findings=findings,
            lineage=lineage,
        )
