"""Streamlit UI for user-approved cleaning and quality comparison."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from business_analyst.cleaning import CleaningEngine, CleaningOperation
from business_analyst.cleaning.comparison import compare_quality
from business_analyst.quality import QualityRules


def render_cleaning_dashboard(
    dataframe: pd.DataFrame,
    rules: QualityRules | None = None,
    workspace_key: str = "default",
) -> None:
    """Let users configure, approve and review cleaning operations."""
    original_key = f"{workspace_key}_original"
    cleaned_key = f"{workspace_key}_cleaned"
    audit_key = f"{workspace_key}_audit"
    plan_key = f"{workspace_key}_cleaning_plan"

    if original_key not in st.session_state:
        st.session_state[original_key] = dataframe.copy(deep=True)
        st.session_state[cleaned_key] = dataframe.copy(deep=True)
        st.session_state[audit_key] = []
        st.session_state[plan_key] = []

    original = st.session_state[original_key]

    st.subheader("Data cleaning")
    st.caption(
        "Choose a transformation, review its parameters, and approve it "
        "before execution. The original dataset remains unchanged."
    )

    available_columns = [str(column) for column in original.columns]
    operation_type = st.selectbox(
        "Transformation",
        [
            "fill_missing",
            "drop_missing",
            "drop_duplicates",
            "convert_numeric",
            "convert_date",
            "trim_text",
            "normalize_category",
        ],
        key=f"{workspace_key}_operation_type",
    )

    selected_columns = st.multiselect(
        "Target columns",
        available_columns,
        key=f"{workspace_key}_selected_columns",
    )

    parameters: dict[str, object] = {}

    if operation_type == "fill_missing":
        strategy = st.selectbox(
            "Fill strategy",
            ["constant", "mean", "median", "mode"],
            key=f"{workspace_key}_fill_strategy",
        )
        parameters["strategy"] = strategy

        if strategy == "constant":
            parameters["value"] = st.text_input(
                "Replacement value",
                value="Unknown",
                key=f"{workspace_key}_fill_value",
            )

    elif operation_type == "drop_duplicates":
        parameters["keep"] = st.selectbox(
            "Which duplicate to keep?",
            ["first", "last"],
            key=f"{workspace_key}_duplicate_keep",
        )

    elif operation_type == "convert_numeric":
        parameters["errors"] = st.selectbox(
            "Invalid numeric values",
            ["raise", "coerce"],
            key=f"{workspace_key}_numeric_errors",
            help=(
                "'raise' stops on invalid values. 'coerce' turns them "
                "into missing values and records the affected cells."
            ),
        )

    elif operation_type == "convert_date":
        parameters["errors"] = st.selectbox(
            "Invalid date values",
            ["raise", "coerce"],
            key=f"{workspace_key}_date_errors",
        )
        date_format = st.text_input(
            "Expected date format (optional)",
            placeholder="%Y-%m-%d",
            key=f"{workspace_key}_date_format",
        )
        if date_format.strip():
            parameters["format"] = date_format.strip()

    elif operation_type == "normalize_category":
        parameters["case"] = st.selectbox(
            "Standardization",
            ["lower", "upper", "title", "preserve"],
            key=f"{workspace_key}_category_case",
        )

    st.markdown("#### Preview current data")
    st.dataframe(
        st.session_state[cleaned_key].head(20),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Approve and apply")
    approved = st.checkbox(
        "I approve this transformation and its parameters.",
        key=f"{workspace_key}_approve_operation",
    )

    if st.button(
        "Apply transformation",
        key=f"{workspace_key}_apply_operation",
        type="primary",
    ):
        if not approved:
            st.warning("Approve the transformation before applying it.")
        elif operation_type != "drop_duplicates" and not selected_columns:
            st.warning("Select at least one target column.")
        else:
            operation = CleaningOperation(
                operation_type=operation_type,
                columns=tuple(selected_columns),
                parameters=parameters,
                approved=True,
            )

            result = CleaningEngine().run(
                st.session_state[cleaned_key],
                [operation],
            )

            st.session_state[cleaned_key] = result.dataframe
            st.session_state[audit_key].extend(result.audit_as_dicts())

            last_record = result.audit_trail[-1]
            if last_record.status == "applied":
                st.success(last_record.summary)
            else:
                st.error(last_record.summary)

    st.markdown("#### Before-and-after quality comparison")
    comparison = compare_quality(
        st.session_state[original_key],
        st.session_state[cleaned_key],
        rules,
    )

    left, right = st.columns(2)
    with left:
        st.markdown("**Before cleaning**")
        st.metric("Rows", comparison.rows_before)
        st.metric("Quality issues", comparison.issues_before)
        st.metric("Missing cells", comparison.missing_cells_before)
        st.metric("Duplicate rows", comparison.duplicate_rows_before)

    with right:
        st.markdown("**After cleaning**")
        st.metric(
            "Rows",
            comparison.rows_after,
            delta=comparison.rows_after - comparison.rows_before,
        )
        st.metric(
            "Quality issues",
            comparison.issues_after,
            delta=comparison.issues_after - comparison.issues_before,
            delta_color="inverse",
        )
        st.metric(
            "Missing cells",
            comparison.missing_cells_after,
            delta=(comparison.missing_cells_after - comparison.missing_cells_before),
            delta_color="inverse",
        )
        st.metric(
            "Duplicate rows",
            comparison.duplicate_rows_after,
            delta=(comparison.duplicate_rows_after - comparison.duplicate_rows_before),
            delta_color="inverse",
        )

    st.markdown("#### Transformation audit trail")
    audit = st.session_state[audit_key]
    if audit:
        st.dataframe(
            pd.DataFrame(audit),
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "Export audit trail (CSV)",
            data=pd.DataFrame(audit).to_csv(index=False).encode("utf-8"),
            file_name="cleaning_audit.csv",
            mime="text/csv",
            key=f"{workspace_key}_download_audit",
        )
    else:
        st.info("No cleaning operations have been applied yet.")

    st.markdown("#### Cleaned dataset")
    st.dataframe(
        st.session_state[cleaned_key],
        use_container_width=True,
        hide_index=True,
    )

    csv_bytes = st.session_state[cleaned_key].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download cleaned CSV",
        data=csv_bytes,
        file_name="cleaned_dataset.csv",
        mime="text/csv",
        key=f"{workspace_key}_download_cleaned",
    )
