"""Streamlit entry point for the AI Business Analyst application."""

from __future__ import annotations

import streamlit as st

from business_analyst.analysis.dashboard import render_analysis_dashboard
from business_analyst.cleaning.comparison import compare_quality
from business_analyst.cleaning.dashboard import render_cleaning_dashboard
from business_analyst.config import get_settings
from business_analyst.exceptions import IngestionError
from business_analyst.ingestion import DataIngestionService
from business_analyst.insights.dashboard import render_insight_dashboard
from business_analyst.quality.dashboard import render_quality_dashboard
from business_analyst.quality.rules import QualityRules
from business_analyst.reporting.dashboard import render_reporting_dashboard
from business_analyst.synthetic_data import retail_sales_csv_bytes


# ---------------------------------------------------------
# Application configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="AI Business Analyst",
    page_icon="📊",
    layout="wide",
)

settings = get_settings()
ingestion_service = DataIngestionService(settings)

st.title("AI Business Analyst")
st.caption(
    "Upload CSV or Excel data to explore data quality, cleaning, "
    "business analysis, AI insights, and reporting."
)


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:
    st.header("Workspace")
    st.info("Authentication and isolated workspaces are planned for later phases.")
    st.caption(f"Current development upload limit: {settings.max_upload_size_mb} MB")


# ---------------------------------------------------------
# File upload and ingestion
# ---------------------------------------------------------

st.subheader("1. Upload a dataset")

uploaded_file = st.file_uploader(
    "Choose a CSV or Excel workbook",
    type=["csv", "xlsx"],
    help=(
        f"Maximum file size: {settings.max_upload_size_mb} MB. "
        "Legacy .xls files are not supported."
    ),
)

if st.button("Load synthetic retail demo"):
    st.session_state["demo_file"] = retail_sales_csv_bytes()
    st.session_state["demo_filename"] = "synthetic_retail_sales.csv"
    st.session_state.pop("ingestion_result", None)

    # Clear all downstream results for the new dataset.
    keys_to_clear = (
        "uploaded_dataset_original",
        "uploaded_dataset_cleaned",
        "uploaded_dataset_audit",
        "uploaded_dataset_cleaning_plan",
        "uploaded_dataset_analysis_result",
        "uploaded_dataset_insights_analysis_result",
        "uploaded_dataset_insights_insight_report",
        "uploaded_dataset_insights_report",
        "uploaded_dataset_report",
    )

    for key in keys_to_clear:
        st.session_state.pop(key, None)


file_bytes: bytes | None = None
filename: str | None = None

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    filename = uploaded_file.name

elif "demo_file" in st.session_state:
    file_bytes = st.session_state["demo_file"]
    filename = st.session_state["demo_filename"]


if file_bytes is not None and filename is not None:
    st.caption(f"Selected file: {filename}")

    selected_sheet: str | None = None

    try:
        if filename.lower().endswith(".xlsx"):
            sheets = ingestion_service.list_sheets(
                filename,
                file_bytes,
            )

            if not sheets:
                st.error("This workbook does not contain any worksheets.")
                st.stop()

            selected_sheet = st.selectbox(
                "Select worksheet",
                options=sheets,
                help="Choose the worksheet to analyze.",
            )

        if st.button("Load dataset", type="primary"):
            result = ingestion_service.ingest(
                filename,
                file_bytes,
                sheet_name=selected_sheet,
            )

            st.session_state["ingestion_result"] = result

            # Reset all downstream state for the newly loaded dataset.
            keys_to_clear = (
                "uploaded_dataset_original",
                "uploaded_dataset_cleaned",
                "uploaded_dataset_audit",
                "uploaded_dataset_cleaning_plan",
                "uploaded_dataset_analysis_result",
                "uploaded_dataset_insights_analysis_result",
                "uploaded_dataset_insights_insight_report",
                "uploaded_dataset_insights_report",
                "uploaded_dataset_report",
            )

            for key in keys_to_clear:
                st.session_state.pop(key, None)

            st.success("Dataset loaded successfully.")

    except IngestionError as exc:
        st.error(exc.message)
        st.session_state.pop("ingestion_result", None)

    except Exception:
        st.error("The file could not be loaded. Check the format and try again.")
        st.session_state.pop("ingestion_result", None)


# ---------------------------------------------------------
# Retrieve ingested dataset
# ---------------------------------------------------------

result = st.session_state.get("ingestion_result")

if result is None:
    st.info(
        "Upload a CSV or Excel file, or load the synthetic demo, "
        "then click 'Load dataset' to continue."
    )
    st.stop()

dataframe = result.dataframe


# ---------------------------------------------------------
# Phase 1: Dataset overview and preview
# ---------------------------------------------------------

st.subheader("2. Dataset overview")

col1, col2, col3 = st.columns(3)

col1.metric("Rows", f"{result.row_count:,}")
col2.metric("Columns", f"{result.column_count:,}")
col3.metric(
    "File size",
    f"{result.source.file_size_bytes:,} bytes",
)

with st.expander("Source metadata", expanded=True):
    st.json(
        {
            "filename": result.source.filename,
            "format": result.source.file_format,
            "encoding": result.source.encoding,
            "delimiter": result.source.delimiter,
            "worksheet": result.source.sheet_name,
            "column_names": list(result.column_names),
        }
    )

st.subheader("3. Data preview")

st.dataframe(
    dataframe.head(100),
    use_container_width=True,
    hide_index=True,
)


# ---------------------------------------------------------
# Phase 2: Data quality
# ---------------------------------------------------------

st.subheader("4. Data quality")

rules = QualityRules(max_missing_fraction=0.05)

render_quality_dashboard(dataframe, rules)


# ---------------------------------------------------------
# Phase 3: Data cleaning
# ---------------------------------------------------------

st.subheader("5. Data cleaning")

render_cleaning_dashboard(
    dataframe,
    workspace_key="uploaded_dataset",
)


# ---------------------------------------------------------
# Retrieve cleaning workspace state
# ---------------------------------------------------------

original_dataframe = st.session_state.get(
    "uploaded_dataset_original",
    dataframe,
)

cleaned_dataframe = st.session_state.get(
    "uploaded_dataset_cleaned",
    dataframe,
)

cleaning_audit = st.session_state.get(
    "uploaded_dataset_audit",
    [],
)


# ---------------------------------------------------------
# Compare data quality before and after cleaning
# ---------------------------------------------------------

quality_comparison = None

try:
    comparison_result = compare_quality(
        original_dataframe,
        cleaned_dataframe,
    )

    quality_comparison = vars(comparison_result)

except (TypeError, ValueError, KeyError):
    quality_comparison = None


# ---------------------------------------------------------
# Phase 4: Business analysis
# ---------------------------------------------------------

st.subheader("6. Business analysis")

render_analysis_dashboard(
    cleaned_dataframe,
    original_dataframe=original_dataframe,
    audit_trail=cleaning_audit,
    quality_comparison=quality_comparison or {},
    workspace_key="uploaded_dataset",
)

# Retrieve the latest successful Phase 4 result AFTER the
# dashboard renders, because analysis runs from its own button.
analysis_result = st.session_state.get("uploaded_dataset_analysis_result")


# ---------------------------------------------------------
# Phase 5: AI insights
# ---------------------------------------------------------

st.subheader("7. AI insights")

if analysis_result is not None:
    render_insight_dashboard(
        analysis_result,
        workspace_key="uploaded_dataset_insights",
    )
else:
    st.info("Run the business analysis first to generate AI insights.")

# Retrieve the saved Phase 5 report after its dashboard renders.
insight_report = st.session_state.get("uploaded_dataset_insights_insight_report")


# ---------------------------------------------------------
# Phase 6: Reporting dashboard
# ---------------------------------------------------------

st.subheader("8. Reports")

render_reporting_dashboard(
    original_dataframe=original_dataframe,
    cleaned_dataframe=cleaned_dataframe,
    quality_report=None,
    quality_comparison=quality_comparison,
    cleaning_audit=cleaning_audit,
    analysis_result=analysis_result,
    insight_report=insight_report,
    workspace_key="uploaded_dataset",
)
