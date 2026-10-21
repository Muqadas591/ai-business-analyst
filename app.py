"""Streamlit entry point for the ingestion workflow."""

from __future__ import annotations

import streamlit as st

from business_analyst.config import get_settings
from business_analyst.exceptions import IngestionError
from business_analyst.ingestion import DataIngestionService
from business_analyst.quality.dashboard import render_quality_dashboard
from business_analyst.quality.rules import QualityRules
from business_analyst.synthetic_data import retail_sales_csv_bytes

st.set_page_config(
    page_title="AI Business Analyst",
    page_icon="📊",
    layout="wide",
)

settings = get_settings()
ingestion_service = DataIngestionService(settings)

st.title("AI Business Analyst")
st.caption(
    "Phase 1 — Secure file ingestion foundation. Upload CSV or Excel data to begin."
)

with st.sidebar:
    st.header("Workspace")
    st.info("Authentication and isolated workspaces are planned for later phases.")
    st.caption(f"Current development upload limit: {settings.max_upload_size_mb} MB")

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
            st.success("Dataset loaded successfully.")

    except IngestionError as exc:
        st.error(exc.message)
        st.session_state.pop("ingestion_result", None)

    except Exception:
        st.error("The file could not be loaded. Check the format and try again.")
        st.session_state.pop("ingestion_result", None)

result = st.session_state.get("ingestion_result")

if result is not None:
    st.subheader("2. Dataset overview")

    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", f"{result.row_count:,}")
    col2.metric("Columns", f"{result.column_count:,}")
    col3.metric("File size", f"{result.source.file_size_bytes:,} bytes")

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
        result.dataframe.head(100),
        use_container_width=True,
        hide_index=True,
    )

    st.info(
        "Ingestion is complete. Data quality validation, cleaning, "
        "visual analytics, AI insights, and report generation will be "
        "added in subsequent phases."
    )
rules = QualityRules(
    max_missing_fraction=0.05,
)

render_quality_dashboard(st.dataframe, rules)
