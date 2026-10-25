"""Product overview and workflow navigation for AI Business Analyst."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


def _value_or(value: Any, fallback: str = "Not available") -> str:
    """Return a safe display value."""
    if value is None:
        return fallback

    return str(value)


def _get_kpis(analysis_result: Any) -> list[Any]:
    """Extract KPI objects from an existing analysis result."""
    if analysis_result is None:
        return []

    kpis = getattr(analysis_result, "kpis", None)

    if isinstance(kpis, list):
        return kpis

    return []


def _get_insights(insight_report: Any) -> list[Any]:
    """Extract validated insight objects from an existing insight report."""
    if insight_report is None:
        return []

    insights = getattr(insight_report, "insights", None)

    if isinstance(insights, list):
        return insights

    return []


def render_product_overview(
    *,
    dataframe: pd.DataFrame | None,
    original_dataframe: pd.DataFrame | None = None,
    analysis_result: Any = None,
    insight_report: Any = None,
    report_artifacts: dict[str, Any] | None = None,
    workspace_name: str = "Current workspace",
    is_demo: bool = False,
) -> None:
    """Render the product overview without running expensive pipeline stages."""
    st.header("Workspace overview")

    st.caption(
        "Review dataset readiness, data quality, calculated KPIs, "
        "AI insights, and available exports."
    )

    # Navigation links target existing headings in the main application.
    with st.sidebar:
        st.subheader("Navigate")

        st.markdown(
            """
            - [Overview](#workspace-overview)
            - [Upload data](#1-upload-a-dataset)
            - [Dataset details](#2-dataset-overview)
            - [Data quality](#4-data-quality)
            - [Data cleaning](#5-data-cleaning)
            - [Business analysis](#6-business-analysis)
            - [AI insights](#7-ai-insights)
            - [Reports](#8-reports)
            """
        )

    if is_demo:
        st.info(
            "Demo mode: this workspace uses synthetic demonstration data. "
            "No real customer or confidential business records are required."
        )

    st.caption(f"Workspace: {workspace_name}")

    if dataframe is None:
        st.info(
            "No dataset is loaded. Upload a CSV or Excel file, or load "
            "the synthetic retail demo, to begin."
        )

        st.markdown("### Recommended workflow")
        st.markdown(
            """
            1. Load a dataset.
            2. Review data-quality findings.
            3. Apply and inspect cleaning operations.
            4. Run business analysis.
            5. Review AI recommendations.
            6. Generate PDF and Excel reports.
            """
        )
        return

    row_count, column_count = dataframe.shape
    missing_cells = int(dataframe.isna().sum().sum())
    total_cells = max(row_count * column_count, 1)
    missing_fraction = missing_cells / total_cells

    duplicate_rows = int(dataframe.duplicated().sum())

    if original_dataframe is None:
        original_row_count = row_count
    else:
        original_row_count = len(original_dataframe)

    kpis = _get_kpis(analysis_result)
    insights = _get_insights(insight_report)
    has_reports = bool(report_artifacts)

    st.subheader("Dataset status")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Rows", f"{row_count:,}")
    col2.metric("Columns", f"{column_count:,}")
    col3.metric("Missing cells", f"{missing_cells:,}")
    col4.metric("Duplicate rows", f"{duplicate_rows:,}")

    if missing_fraction == 0 and duplicate_rows == 0:
        st.success("Basic quality checks: no missing cells or duplicate rows.")
    else:
        st.warning(
            f"Basic quality checks found {missing_cells:,} missing cells "
            f"and {duplicate_rows:,} duplicate rows. Review the data-quality "
            "and cleaning sections before relying on the results."
        )

    st.caption(
        f"Rows before cleaning: {original_row_count:,} · "
        f"Rows currently loaded: {row_count:,}"
    )

    st.subheader("Analysis and deliverables")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Calculated KPIs",
        len(kpis),
        help="KPIs from the latest analysis result available in this session.",
    )
    col2.metric(
        "Validated AI insights",
        len(insights),
        help="Insights from the latest validated AI report available in this session.",
    )
    col3.metric(
        "Reports",
        "Ready" if has_reports else "Not generated",
    )

    if analysis_result is None:
        st.info("Run business analysis to calculate KPIs.")
    elif not kpis:
        st.info(
            "An analysis result exists, but it does not contain KPIs. "
            "Review the selected business metrics."
        )
    else:
        st.markdown("#### KPI highlights")

        for kpi in kpis[:5]:
            name = _value_or(getattr(kpi, "name", None), "KPI")
            value = getattr(kpi, "value", None)
            description = getattr(kpi, "description", None)

            col1, col2 = st.columns([1, 2])

            with col1:
                st.write(f"**{name}**")
                st.write(_value_or(value))

            with col2:
                if description:
                    st.caption(str(description))

    if insight_report is None:
        st.info(
            "AI insights have not been generated for the current session, "
            "or they were cleared after a dataset change."
        )
    else:
        st.markdown("#### AI insight review")

        summary = getattr(insight_report, "executive_summary", None)

        if summary:
            st.write(summary)

        st.caption(
            "AI-generated recommendations are advisory. Check the cited "
            "evidence and validate important conclusions before acting."
        )

        for insight in insights[:3]:
            title = _value_or(getattr(insight, "title", None), "Insight")
            observation = getattr(insight, "observation", None)
            recommendation = getattr(insight, "recommendation", None)

            with st.expander(title):
                if observation:
                    st.write("**Evidence:**")
                    st.write(observation)

                if recommendation:
                    st.write("**Suggested next step:**")
                    st.write(recommendation)

    if has_reports:
        st.success(
            "Report artifacts are available. Open the Reports section "
            "to review and download the generated files."
        )
    else:
        st.info(
            "PDF and Excel downloads will become available after reports "
            "have been generated successfully."
        )

    st.divider()

    st.markdown("### Next recommended action")

    if missing_cells or duplicate_rows:
        st.write("**1.** Review data quality and clean the dataset.")
    elif analysis_result is None:
        st.write("**1.** Run business analysis and review the KPIs.")
    elif insight_report is None:
        st.write("**1.** Generate and review AI insights.")
    elif not has_reports:
        st.write("**1.** Generate PDF and Excel reports.")
    else:
        st.write(
            "**Ready for review.** Confirm the data, recommendations, "
            "and report contents before sharing."
        )