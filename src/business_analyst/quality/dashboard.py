"""Streamlit presentation for data-quality reports."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import streamlit as st

from business_analyst.quality import DataQualityEngine, QualityRules


def render_quality_dashboard(
    dataframe: pd.DataFrame,
    rules: QualityRules | None = None,
) -> None:
    """Display profiling and validation results for a DataFrame."""
    report = DataQualityEngine(rules).run(dataframe)

    st.subheader("Data quality overview")
    st.caption(
        "Review these findings before cleaning. The source dataset "
        "has not been modified."
    )

    first, second, third, fourth = st.columns(4)
    first.metric("Rows", f"{report.row_count:,}")
    second.metric("Columns", f"{report.column_count:,}")
    third.metric("Issues", f"{report.issue_count:,}")
    fourth.metric("Affected rows", f"{report.affected_row_count:,}")

    if report.error_count:
        st.error(f"{report.error_count} error-level findings")
    if report.warning_count:
        st.warning(f"{report.warning_count} warning-level findings")
    if not report.issues and not report.schema_errors:
        st.success("No issues were detected by the configured checks.")

    if report.issues:
        st.markdown("#### Issues to investigate")

        issue_records = [
            {
                "Code": issue.code,
                "Severity": issue.severity,
                "Category": issue.category,
                "Column": issue.column or "—",
                "Affected rows": issue.affected_rows,
                "Message": issue.message,
                "Example values": ", ".join(issue.examples),
                "Recommended action": issue.recommendation,
                "Row numbers": ", ".join(
                    str(number) for number in issue.row_numbers[:30]
                ),
            }
            for issue in report.issues
        ]

        issues_df = pd.DataFrame(issue_records)

        severity_filter = st.multiselect(
            "Filter by severity",
            options=["error", "warning"],
            default=["error", "warning"],
            key="quality_severity_filter",
        )

        filtered = issues_df[issues_df["Severity"].isin(severity_filter)]
        st.dataframe(filtered, use_container_width=True, hide_index=True)

    if report.schema_errors:
        with st.expander("Pandera schema validation details"):
            st.write(f"{len(report.schema_errors)} schema finding(s)")
            st.dataframe(
                pd.DataFrame({"Schema validation finding": report.schema_errors}),
                use_container_width=True,
                hide_index=True,
            )

    with st.expander("Column profiles"):
        profile_df = pd.DataFrame([asdict(profile) for profile in report.profiles])
        if not profile_df.empty:
            st.dataframe(
                profile_df,
                use_container_width=True,
                hide_index=True,
            )

    with st.expander("Preview original data"):
        st.dataframe(dataframe.head(100), use_container_width=True)
