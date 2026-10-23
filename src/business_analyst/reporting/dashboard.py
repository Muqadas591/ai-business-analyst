from __future__ import annotations

import streamlit as st
import pandas as pd

from business_analyst.reporting import ReportingEngine, ReportInputs


def render_reporting_dashboard(
    original_dataframe: pd.DataFrame | None,
    cleaned_dataframe: pd.DataFrame | None,
    *,
    quality_report=None,
    quality_comparison=None,
    cleaning_audit=None,
    analysis_result=None,
    insight_report=None,
    workspace_key: str = "uploaded_dataset",
) -> None:
    st.header("Business Reports")
    st.caption("Generate shareable PDF and Excel deliverables from your analysis.")

    if original_dataframe is None:
        st.info("Upload a dataset before generating a report.")
        return

    if cleaned_dataframe is None:
        cleaned_dataframe = original_dataframe

    analysis_result = analysis_result or st.session_state.get(
        f"{workspace_key}_analysis_result"
    )
    insight_report = insight_report or st.session_state.get(
        f"{workspace_key}_insight_report"
    )

    st.warning(
        "Review exported reports before sharing. They may contain sensitive "
        "business information. AI recommendations are advisory and require "
        "human review."
    )

    include_analysis = analysis_result is not None
    include_insights = insight_report is not None

    st.write(f"Original rows: **{len(original_dataframe):,}**")
    st.write(f"Rows in report: **{len(cleaned_dataframe):,}**")
    st.write(f"Analysis available: **{'Yes' if include_analysis else 'No'}**")
    st.write(f"AI recommendations available: **{'Yes' if include_insights else 'No'}**")

    dataset_name = st.text_input(
        "Report title",
        value="Business Analysis",
        max_chars=120,
        key=f"{workspace_key}_report_title",
    )

    if st.button(
        "Generate PDF and Excel reports",
        type="primary",
        key=f"{workspace_key}_generate_reports",
    ):
        try:
            with st.spinner("Building reports..."):
                inputs = ReportInputs(
                    dataset_name=dataset_name.strip() or "Business Analysis",
                    original_dataframe=original_dataframe,
                    cleaned_dataframe=cleaned_dataframe,
                    quality_report=quality_report,
                    quality_comparison=quality_comparison,
                    cleaning_audit=cleaning_audit,
                    analysis_result=analysis_result,
                    insight_report=insight_report,
                )
                artifacts = ReportingEngine().generate(inputs)

            st.session_state[f"{workspace_key}_report_artifacts"] = {
                "pdf_bytes": artifacts.pdf_bytes,
                "excel_bytes": artifacts.excel_bytes,
                "pdf_filename": artifacts.pdf_filename,
                "excel_filename": artifacts.excel_filename,
                "report_data": artifacts.report_data,
            }
            st.success("Both reports were generated successfully.")

        except (ValueError, RuntimeError) as exc:
            st.error(f"Could not generate the reports: {exc}")
            return
        except Exception:
            # Avoid displaying stack traces, secrets, or raw provider data.
            st.error(
                "An unexpected reporting error occurred. Check the "
                "application logs for diagnostic details."
            )
            return

    artifacts = st.session_state.get(f"{workspace_key}_report_artifacts")
    if not artifacts:
        st.caption("Generate the reports to enable downloads.")
        return

    left, right = st.columns(2)

    with left:
        st.download_button(
            "Download PDF report",
            data=artifacts["pdf_bytes"],
            file_name=artifacts["pdf_filename"],
            mime="application/pdf",
            key=f"{workspace_key}_download_pdf",
        )

    with right:
        st.download_button(
            "Download Excel workbook",
            data=artifacts["excel_bytes"],
            file_name=artifacts["excel_filename"],
            mime=("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            key=f"{workspace_key}_download_excel",
        )

    with st.expander("Preview report contents"):
        report_data = artifacts["report_data"]
        st.json(
            {
                "dataset": report_data.get("dataset"),
                "quality": report_data.get("quality"),
                "cleaning": report_data.get("cleaning"),
                "kpi_count": len(report_data.get("analysis", {}).get("kpis", {})),
                "recommendation_count": len(
                    report_data.get("insights", {}).get("insights", [])
                ),
                "limitations": report_data.get("limitations"),
            }
        )
