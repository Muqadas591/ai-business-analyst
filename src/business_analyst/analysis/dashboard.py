"""Streamlit dashboard for EDA and business KPIs."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from business_analyst.analysis import AnalysisEngine
from business_analyst.analysis.models import KPIResult


def _column_selector(
    label: str,
    columns: list[str],
    key: str,
    allow_none: bool = True,
) -> str | None:
    options = (["— Not selected —"] if allow_none else []) + columns
    selected = st.selectbox(label, options=options, key=key)

    if allow_none and selected == "— Not selected —":
        return None
    return selected


def _format_kpi(kpi: KPIResult) -> str:
    if kpi.status != "ok" or kpi.value is None:
        return "Not available"

    if kpi.format == "percentage":
        return f"{kpi.value:,.2f}%"
    if kpi.format == "currency":
        return f"{kpi.value:,.2f}"
    return f"{kpi.value:,.2f}"


def render_analysis_dashboard(
    dataframe: pd.DataFrame,
    *,
    original_dataframe: pd.DataFrame | None = None,
    audit_trail: list[dict] | None = None,
    quality_comparison: dict | None = None,
    workspace_key: str = "analysis",
) -> None:
    """Render EDA, KPI, trend, group, and finding views."""

    st.header("Exploratory Data Analysis & Business KPIs")

    if dataframe.empty:
        st.warning("The cleaned dataset contains no rows to analyze.")
        return

    columns = [str(column) for column in dataframe.columns]
    numeric_columns = [
        str(column) for column in dataframe.select_dtypes(include="number").columns
    ]

    if not numeric_columns:
        st.info(
            "No numeric columns were detected. Convert relevant columns "
            "to numeric in the cleaning workspace before calculating KPIs."
        )

    with st.expander("Configure business metrics", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            revenue_column = _column_selector(
                "Revenue column",
                numeric_columns,
                f"{workspace_key}_revenue",
            )
            profit_column = _column_selector(
                "Profit column",
                numeric_columns,
                f"{workspace_key}_profit",
            )
            quantity_column = _column_selector(
                "Quantity column",
                numeric_columns,
                f"{workspace_key}_quantity",
            )

        with col2:
            order_id_column = _column_selector(
                "Order ID column",
                columns,
                f"{workspace_key}_order_id",
            )
            date_column = _column_selector(
                "Date column",
                columns,
                f"{workspace_key}_date",
            )
            group_column = _column_selector(
                "Group by column",
                columns,
                f"{workspace_key}_group",
            )

        trend_metric_column = _column_selector(
            "Metric for time trend",
            numeric_columns,
            f"{workspace_key}_trend_metric",
        )
        group_metric_column = _column_selector(
            "Metric for group comparison",
            numeric_columns,
            f"{workspace_key}_group_metric",
        )

        frequency = st.selectbox(
            "Trend frequency",
            ["D", "W", "M", "Q", "Y"],
            index=2,
            key=f"{workspace_key}_frequency",
            help="D=daily, W=weekly, M=monthly, Q=quarterly, Y=yearly.",
        )

        aggregation = st.selectbox(
            "Group aggregation",
            ["sum", "mean", "median", "count"],
            key=f"{workspace_key}_aggregation",
        )

    if not st.button(
        "Run analysis",
        type="primary",
        key=f"{workspace_key}_run",
    ):
        st.caption("Configure the columns above and run the analysis.")
        return

    try:
        result = AnalysisEngine().run(
            dataframe,
            dataset_id=workspace_key,
            revenue_column=revenue_column,
            profit_column=profit_column,
            order_id_column=order_id_column,
            quantity_column=quantity_column,
            date_column=date_column,
            trend_metric_column=trend_metric_column,
            trend_frequency=frequency,
            group_column=group_column,
            group_metric_column=group_metric_column,
            group_aggregation=aggregation,
            original_dataframe=original_dataframe,
            audit_trail=audit_trail,
            quality_comparison=quality_comparison,
        )
    except (TypeError, ValueError) as exc:
        st.error(f"Analysis could not be completed: {exc}")
        return

    st.subheader("Dataset overview")
    m1, m2 = st.columns(2)
    m1.metric("Rows analyzed", f"{result.row_count:,}")
    m2.metric("Columns analyzed", f"{result.column_count:,}")

    st.subheader("Business KPIs")
    if result.kpis:
        kpi_columns = st.columns(min(3, len(result.kpis)))
        for index, kpi in enumerate(result.kpis):
            with kpi_columns[index % len(kpi_columns)]:
                st.metric(kpi.name, _format_kpi(kpi))
                st.caption(kpi.description)
    else:
        st.info("Select at least one business metric to calculate KPIs.")

    st.subheader("Numeric distributions")
    if result.numeric_profiles:
        profile_frame = pd.DataFrame(result.numeric_profiles).T
        st.dataframe(profile_frame, use_container_width=True)

        selected_numeric = st.selectbox(
            "Numeric column to visualize",
            list(result.numeric_profiles),
            key=f"{workspace_key}_numeric_chart",
        )
        values = dataframe[selected_numeric].dropna()
        if not values.empty:
            fig = px.histogram(
                x=values,
                nbins=30,
                title=f"Distribution of {selected_numeric}",
                labels={"x": selected_numeric, "y": "Count"},
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No numeric distributions are available.")

    st.subheader("Categorical distributions")
    if result.categorical_profiles:
        selected_category = st.selectbox(
            "Category column",
            list(result.categorical_profiles),
            key=f"{workspace_key}_category_chart",
        )
        category_frame = pd.DataFrame(result.categorical_profiles[selected_category])
        st.dataframe(category_frame, use_container_width=True)

        if not category_frame.empty:
            fig = px.bar(
                category_frame,
                x="category",
                y="count",
                title=f"Most frequent values: {selected_category}",
            )
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Time trends")
    if result.trends:
        trend_key = next(iter(result.trends))
        trend_frame = pd.DataFrame(result.trends[trend_key])
        st.dataframe(trend_frame, use_container_width=True)
        fig = px.line(
            trend_frame,
            x="period",
            y="value",
            markers=True,
            title=trend_key,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select both a date column and a numeric trend metric.")

    st.subheader("Grouped business summaries")
    if result.grouped_summaries:
        for key, rows in result.grouped_summaries.items():
            st.markdown(f"**{key}**")
            group_frame = pd.DataFrame(rows)
            st.dataframe(group_frame, use_container_width=True)
            if not group_frame.empty:
                fig = px.bar(
                    group_frame,
                    x="group",
                    y="value",
                    title=key,
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select a grouping column and a numeric metric.")

    st.subheader("Numeric correlations")
    if result.correlations:
        correlation_frame = pd.DataFrame(result.correlations)
        st.dataframe(correlation_frame, use_container_width=True)

        matrix = dataframe.select_dtypes(include="number").corr()
        if matrix.shape[0] >= 2:
            fig = px.imshow(
                matrix,
                text_auto=".2f",
                aspect="auto",
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1,
                title="Pearson correlation matrix",
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("At least two numeric columns with sufficient valid data are needed.")

    st.subheader("Evidence-backed findings")
    if result.findings:
        for finding in result.findings:
            with st.expander(finding.title):
                st.write(finding.description)
                st.json(finding.evidence)
                if finding.limitations:
                    st.caption("Limitations: " + " ".join(finding.limitations))
    else:
        st.info("No findings could be generated from the selected analysis.")

    st.subheader("Preparation lineage")
    st.write(
        "The analyzed dataset is linked to the supplied preparation metadata. "
        "A fingerprint identifies the current DataFrame representation."
    )
    st.json(result.lineage)
    st.session_state[f"{workspace_key}_analysis_result"] = result
    st.download_button(
        "Downl oad analysis results (JSON)",
        data=__import__("json").dumps(result.to_dict(), indent=2, default=str),
        file_name="business_analysis.json",
        mime="application/json",
        key=f"{workspace_key}_download_json",
    )
