"""Streamlit entry point for the AI Business Analyst application."""

from __future__ import annotations

import hashlib
import json
import logging

import pandas as pd
import streamlit as st
from business_analyst.auth_ui import (
    render_authentication_and_workspace_selector,
)
from business_analyst.analysis.dashboard import render_analysis_dashboard
from business_analyst.cleaning.comparison import compare_quality
from business_analyst.cleaning.dashboard import render_cleaning_dashboard
from business_analyst.config import get_settings
from business_analyst.exceptions import IngestionError
from business_analyst.ingestion import DataIngestionService
from business_analyst.insights.dashboard import render_insight_dashboard
from business_analyst.security.logging_config import (
    configure_logging,
    log_security_event,
)
from business_analyst.quality.dashboard import render_quality_dashboard
from business_analyst.quality.rules import QualityRules
from business_analyst.reporting.dashboard import render_reporting_dashboard
from business_analyst.security import (
    ResourceLimitError,
    require_authenticated_user_id,
    validate_dataframe_size,
    validate_filename,
    validate_upload_size,
)
from business_analyst.synthetic_data import retail_sales_csv_bytes
from business_analyst.workflow import (
    WorkflowStage,
    WorkflowState,
    invalidate_session_results,
    stage_summary,
    synchronize_workflow_state,
)
from business_analyst.workspaces import (
    WorkspaceAccessService,
    workspace_namespace,
)
from business_analyst.workspaces.access import (
    WorkspacePermissionError,
)
from business_analyst.workspaces.models import WorkspaceRole
from business_analyst.product_dashboard import render_product_overview
configure_logging()
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="AI Business Analyst",
    page_icon="📊",
    layout="wide",
)

settings = get_settings()
ingestion_service = DataIngestionService(settings)


# ---------------------------------------------------------
# 1. Authentication and workspace authorization
# ---------------------------------------------------------
_auth_context = render_authentication_and_workspace_selector()
principal = _auth_context["verified_user"]
db_session = _auth_context["db_session"]
selected_workspace_id = _auth_context["selected_workspace_id"]

try:
    # The principal comes from successful application authentication.
    authenticated_user_id = require_authenticated_user_id(principal)
    access = WorkspaceAccessService(db_session)

    # Verify membership before loading workspace-specific data.
    workspace = access.get_accessible_workspace(
        authenticated_user_id=authenticated_user_id,
        workspace_id=selected_workspace_id,
    )
except Exception:
    db_session.close()
    logger.warning(
        "Workspace access verification failed.",
        extra={"event": "workspace_access_denied"},
    )
    st.error("The selected workspace could not be verified or accessed.")
    st.stop()


def stop_app() -> None:
    """Close the database session before stopping the Streamlit run."""
    db_session.close()
    st.stop()


def has_any_role(allowed_roles: set[WorkspaceRole]) -> bool:
    """Check the current user's role against the database."""
    try:
        access.require_role(
            authenticated_user_id=authenticated_user_id,
            workspace_id=workspace.id,
            allowed_roles=allowed_roles,
        )
        return True
    except WorkspacePermissionError:
        return False


def require_editor_access() -> None:
    """Require owner/editor permission before modifying or processing data."""
    access.require_role(
        authenticated_user_id=authenticated_user_id,
        workspace_id=workspace.id,
        allowed_roles={
            WorkspaceRole.OWNER,
            WorkspaceRole.EDITOR,
        },
    )


def require_owner_access() -> None:
    """Require owner permission for owner-only operations."""
    access.require_role(
        authenticated_user_id=authenticated_user_id,
        workspace_id=workspace.id,
        allowed_roles={WorkspaceRole.OWNER},
    )


can_edit = has_any_role(
    {WorkspaceRole.OWNER, WorkspaceRole.EDITOR}
)
is_owner = has_any_role({WorkspaceRole.OWNER})

workspace_key = workspace_namespace(
    authenticated_user_id=authenticated_user_id,
    workspace_id=workspace.id,
)

WORKSPACE_KEY = workspace_key
INSIGHTS_KEY = f"{workspace_key}_insights"


# ---------------------------------------------------------
# 2. Workspace-specific session state
# ---------------------------------------------------------

# Clear artifacts belonging to the previous workspace namespace.
_previous_workspace_key = st.session_state.get(
    "_active_workspace_namespace"
)

if (
    _previous_workspace_key
    and _previous_workspace_key != workspace_key
):
    for state_key in list(st.session_state.keys()):
        if state_key.startswith(_previous_workspace_key):
            st.session_state.pop(state_key, None)

    st.session_state.pop("workflow_state", None)

st.session_state["_active_workspace_namespace"] = workspace_key


def clear_dataset_state(*, clear_upload: bool = False) -> None:
    """Clear artifacts tied to the currently loaded dataset."""
    keys = [
        f"{WORKSPACE_KEY}_ingestion_result",
        f"{WORKSPACE_KEY}_original",
        f"{WORKSPACE_KEY}_cleaned",
        f"{WORKSPACE_KEY}_audit",
        f"{WORKSPACE_KEY}_cleaning_plan",
        f"{WORKSPACE_KEY}_cleaned_fingerprint",
        f"{WORKSPACE_KEY}_analysis_result",
        f"{INSIGHTS_KEY}_analysis_result",
        f"{INSIGHTS_KEY}_insight_report",
        f"{INSIGHTS_KEY}_report",
        f"{WORKSPACE_KEY}_insight_report",
        f"{WORKSPACE_KEY}_report",
        f"{WORKSPACE_KEY}_report_artifacts",
        "workflow_state",
    ]

    if clear_upload:
        keys.extend(
            [
                f"{WORKSPACE_KEY}_demo_file",
                f"{WORKSPACE_KEY}_demo_filename",
                f"{WORKSPACE_KEY}_selected_worksheet",
            ]
        )

    for key in keys:
        st.session_state.pop(key, None)


def dataframe_fingerprint(dataframe: pd.DataFrame) -> str:
    """Return a fingerprint used to detect in-session data changes."""
    digest = hashlib.sha256()

    digest.update(
        json.dumps(
            [str(column) for column in dataframe.columns],
            ensure_ascii=False,
        ).encode("utf-8")
    )

    digest.update(
        pd.util.hash_pandas_object(
            dataframe,
            index=True,
        ).values.tobytes()
    )

    return digest.hexdigest()


def get_workflow_state() -> WorkflowState:
    """Return the current session's workflow state."""
    state = st.session_state.get("workflow_state")

    if not isinstance(state, WorkflowState):
        state = WorkflowState(dataset_id=WORKSPACE_KEY)
        st.session_state["workflow_state"] = state

    return state


def reject_upload(message: str) -> None:
    """Display and log an upload rejection without exposing sensitive data."""
    st.error(message)

    log_security_event(
        logger,
        event="upload_rejected",
        status_code=400,
    )


# ---------------------------------------------------------
# 3. Application header
# ---------------------------------------------------------

st.title("AI Business Analyst")

st.caption(
    "Upload CSV or Excel data to explore data quality, cleaning, "
    "business analysis, AI insights, and reporting."
)

with st.sidebar:
    st.header("Workspace")
    st.info(
        "The active workspace was verified through authentication "
        "and database membership checks. Dashboard artifacts use a "
        "user/workspace-specific namespace."
    )
    st.caption(
        f"Maximum upload size: {settings.max_upload_size_mb} MB"
    )

    if is_owner:
        st.caption("Workspace role: Owner")
    elif can_edit:
        st.caption("Workspace role: Editor")
    else:
        st.caption("Workspace role: Viewer — read-only data operations")


# ---------------------------------------------------------
# 4. Upload and ingestion
# ---------------------------------------------------------

st.subheader("1. Upload a dataset")

if not can_edit:
    st.info(
        "Your workspace role permits reading available results, "
        "but uploading or processing datasets requires the owner "
        "or editor role."
    )

uploaded_file = st.file_uploader(
    "Choose a CSV or Excel workbook",
    type=["csv", "xlsx"],
    help=(
        f"Maximum file size: {settings.max_upload_size_mb} MB. "
        "Legacy .xls files are not supported."
    ),
    disabled=not can_edit,
)

demo_column, reset_column = st.columns([3, 1])

with demo_column:
    if st.button(
        "Load synthetic retail demo",
        key=f"{WORKSPACE_KEY}_load_retail_demo",
        disabled=not can_edit,
    ):
        try:
            require_editor_access()

            demo_bytes = retail_sales_csv_bytes()
            demo_filename = validate_filename(
                "synthetic_retail_sales.csv"
            )
            validate_upload_size(len(demo_bytes))

            # Clear stale results when replacing the current dataset.
            clear_dataset_state()

            st.session_state[
                f"{WORKSPACE_KEY}_demo_file"
            ] = demo_bytes

            st.session_state[
                f"{WORKSPACE_KEY}_demo_filename"
            ] = demo_filename

            st.rerun()

        except WorkspacePermissionError:
            st.error("Owner or editor permission is required.")
            stop_app()
        except (ValueError, ResourceLimitError) as exc:
            reject_upload(str(exc))
            stop_app()

with reset_column:
    if st.button(
        "Reset workspace",
        key=f"{WORKSPACE_KEY}_reset_workspace",
        disabled=not is_owner,
    ):
        try:
            require_owner_access()
            clear_dataset_state(clear_upload=True)
            st.rerun()
        except WorkspacePermissionError:
            st.error("Only the workspace owner can reset this workspace.")
            stop_app()


# Validate a user-uploaded file before reading its bytes or parsing a workbook.
uploaded_filename: str | None = None

if uploaded_file is not None and can_edit:
    try:
        require_editor_access()

        uploaded_filename = validate_filename(uploaded_file.name)
        validate_upload_size(uploaded_file.size)

    except WorkspacePermissionError:
        st.error("Owner or editor permission is required.")
        stop_app()
    except (ValueError, ResourceLimitError) as exc:
        reject_upload(str(exc))
        stop_app()


file_bytes: bytes | None = None
filename: str | None = None

if uploaded_file is not None and can_edit:
    # Size and filename have already been checked above.
    file_bytes = uploaded_file.getvalue()
    filename = uploaded_filename

elif f"{WORKSPACE_KEY}_demo_file" in st.session_state:
    file_bytes = st.session_state[f"{WORKSPACE_KEY}_demo_file"]
    filename = st.session_state.get(
        f"{WORKSPACE_KEY}_demo_filename"
    )


if file_bytes is not None and filename is not None and can_edit:
    st.caption(f"Selected file: {filename}")

    selected_sheet: str | None = None

    try:
        # A workbook may consume significant memory while being parsed.
        # The ingestion implementation must also enforce workbook parsing
        # limits before loading worksheets into memory.
        if filename.lower().endswith(".xlsx"):
            sheets = ingestion_service.list_sheets(
                filename,
                file_bytes,
            )

            if not sheets:
                st.error("This workbook does not contain any worksheets.")
                stop_app()

            selected_sheet = st.selectbox(
                "Select worksheet",
                options=sheets,
                key=f"{WORKSPACE_KEY}_selected_worksheet",
            )

        if st.button(
            "Load dataset",
            type="primary",
            key=f"{WORKSPACE_KEY}_load_dataset",
        ):
            try:
                # Recheck authorization immediately before processing.
                require_editor_access()

                # Revalidate at the processing boundary.
                safe_filename = validate_filename(filename)
                validate_upload_size(len(file_bytes))

                with st.spinner("Validating and loading dataset..."):
                    ingestion_result = ingestion_service.ingest(
                        safe_filename,
                        file_bytes,
                        sheet_name=selected_sheet,
                    )

                # Enforce row/column limits before profiling or analysis.
                validate_dataframe_size(
                    ingestion_result.dataframe
                )

                # The new dataset was accepted; invalidate dependent results.
                clear_dataset_state()

                st.session_state[
                    f"{WORKSPACE_KEY}_ingestion_result"
                ] = ingestion_result

                st.session_state["workflow_state"] = WorkflowState(
                    dataset_id=WORKSPACE_KEY
                )

                st.success("Dataset loaded successfully.")
                st.rerun()

            except WorkspacePermissionError:
                st.error("Owner or editor permission is required.")
                stop_app()
            except (ValueError, ResourceLimitError) as exc:
                reject_upload(str(exc))
                stop_app()

    except IngestionError as exc:
        st.error(exc.message)
    except (ValueError, ResourceLimitError) as exc:
        reject_upload(str(exc))
    except Exception:
        logger.exception("Dataset ingestion failed.")
        st.error(
            "The file could not be loaded. Check the format and "
            "try again."
        )


# ---------------------------------------------------------
# 5. Read the accepted dataset
# ---------------------------------------------------------

# Recheck membership before reading workspace-specific session data.
try:
    workspace = access.get_accessible_workspace(
        authenticated_user_id=authenticated_user_id,
        workspace_id=selected_workspace_id,
    )
except Exception:
    st.error("Workspace access could not be verified.")
    stop_app()

ingestion_result = st.session_state.get(
    f"{WORKSPACE_KEY}_ingestion_result"
)

# Show the product overview even when no dataset has been loaded.
if ingestion_result is None:
    render_product_overview(
        dataframe=None,
        workspace_name=workspace.name,
    )

    st.info(
        "Upload a CSV or Excel file, or load the synthetic demo, "
        "then click 'Load dataset' to continue."
    )
    stop_app()

dataframe = ingestion_result.dataframe

try:
    validate_dataframe_size(dataframe)
except ValueError as exc:
    clear_dataset_state()
    st.error(f"The stored dataset failed validation: {exc}")
    stop_app()


# ---------------------------------------------------------
# 5A. Product overview
# ---------------------------------------------------------

original_for_overview = st.session_state.get(
    f"{WORKSPACE_KEY}_original",
    dataframe,
)

cleaned_for_overview = st.session_state.get(
    f"{WORKSPACE_KEY}_cleaned",
    dataframe,
)

analysis_for_overview = st.session_state.get(
    f"{WORKSPACE_KEY}_analysis_result"
)

insights_for_overview = st.session_state.get(
    f"{INSIGHTS_KEY}_insight_report"
)

reports_for_overview = st.session_state.get(
    f"{WORKSPACE_KEY}_report_artifacts"
)

is_synthetic_demo = (
    f"{WORKSPACE_KEY}_demo_file" in st.session_state
)

render_product_overview(
    dataframe=dataframe,
    workspace_name=workspace.name,
    original_dataframe=original_for_overview,
    cleaned_dataframe=cleaned_for_overview,
    analysis_result=analysis_for_overview,
    insight_report=insights_for_overview,
    report_artifacts=reports_for_overview,
    is_synthetic_demo=is_synthetic_demo,
)

# ---------------------------------------------------------
# 6. Dataset overview and permitted reads
# ---------------------------------------------------------

st.subheader("2. Dataset overview")

col1, col2, col3 = st.columns(3)

col1.metric("Rows", f"{ingestion_result.row_count:,}")
col2.metric("Columns", f"{ingestion_result.column_count:,}")
col3.metric(
    "File size",
    f"{ingestion_result.source.file_size_bytes:,} bytes",
)

with st.expander("Source metadata", expanded=False):
    st.json(
        {
            "filename": ingestion_result.source.filename,
            "format": ingestion_result.source.file_format,
            "encoding": ingestion_result.source.encoding,
            "delimiter": ingestion_result.source.delimiter,
            "worksheet": ingestion_result.source.sheet_name,
            "column_names": list(ingestion_result.column_names),
        }
    )

st.subheader("3. Data preview")

st.dataframe(
    dataframe.head(100),
    use_container_width=True,
    hide_index=True,
)


# ---------------------------------------------------------
# 7. Data quality
# ---------------------------------------------------------

st.subheader("4. Data quality")

rules = QualityRules(max_missing_fraction=0.05)

# This dashboard is treated as a read-only operation.
render_quality_dashboard(dataframe, rules)


# ---------------------------------------------------------
# 8. Cleaning
# ---------------------------------------------------------

st.subheader("5. Data cleaning")

if can_edit:
    try:
        require_editor_access()

        render_cleaning_dashboard(
            dataframe,
            workspace_key=workspace_key,
        )

    except WorkspacePermissionError:
        st.warning(
            "Cleaning is unavailable because owner or editor "
            "permission is required."
        )
else:
    st.info(
        "Cleaning controls are disabled for viewers. An owner or "
        "editor must perform cleaning operations."
    )

original_dataframe = st.session_state.get(
    f"{WORKSPACE_KEY}_original",
    dataframe,
)

cleaned_dataframe = st.session_state.get(
    f"{WORKSPACE_KEY}_cleaned",
    dataframe,
)

cleaning_audit = st.session_state.get(
    f"{WORKSPACE_KEY}_audit",
    [],
)

# Validate both versions before quality comparison, analysis or reporting.
try:
    validate_dataframe_size(original_dataframe)
    validate_dataframe_size(cleaned_dataframe)
except ValueError as exc:
    st.error(f"Dataset validation failed: {exc}")
    stop_app()


# Invalidate downstream results if the cleaned data changed.
current_fingerprint = dataframe_fingerprint(cleaned_dataframe)

previous_fingerprint = st.session_state.get(
    f"{WORKSPACE_KEY}_cleaned_fingerprint"
)

if (
    previous_fingerprint is not None
    and previous_fingerprint != current_fingerprint
):
    invalidate_session_results(
        st.session_state,
        WorkflowStage.ANALYSIS,
    )

    # Also remove namespaced outputs so they cannot be reused accidentally.
    for key in (
        f"{WORKSPACE_KEY}_analysis_result",
        f"{INSIGHTS_KEY}_analysis_result",
        f"{INSIGHTS_KEY}_insight_report",
        f"{INSIGHTS_KEY}_report",
        f"{WORKSPACE_KEY}_insight_report",
        f"{WORKSPACE_KEY}_report",
        f"{WORKSPACE_KEY}_report_artifacts",
    ):
        st.session_state.pop(key, None)

    st.info(
        "The cleaned dataset changed. Previous analysis, AI insights, "
        "and generated reports were cleared. Run the downstream stages again."
    )

st.session_state[
    f"{WORKSPACE_KEY}_cleaned_fingerprint"
] = current_fingerprint


# ---------------------------------------------------------
# 9. Before/after quality comparison
# ---------------------------------------------------------

quality_comparison = None

try:
    comparison = compare_quality(
        original_dataframe,
        cleaned_dataframe,
        rules=rules,
    )
    quality_comparison = vars(comparison)

except (TypeError, ValueError, KeyError):
    st.warning(
        "The before/after quality comparison could not be created. "
        "The remaining workflow can still be used."
    )


# ---------------------------------------------------------
# 10. Business analysis
# ---------------------------------------------------------

st.subheader("6. Business analysis")

analysis_result = st.session_state.get(
    f"{WORKSPACE_KEY}_analysis_result"
)

if can_edit:
    try:
        # Authorize before invoking a dashboard that can run analysis.
        require_editor_access()

        render_analysis_dashboard(
            cleaned_dataframe,
            original_dataframe=original_dataframe,
            audit_trail=cleaning_audit,
            quality_comparison=quality_comparison or {},
            workspace_key=workspace_key,
        )

    except WorkspacePermissionError:
        st.warning("Owner or editor permission is required for analysis.")

    # Re-read the result in case the dashboard generated it.
    analysis_result = st.session_state.get(
        f"{WORKSPACE_KEY}_analysis_result"
    )

else:
    st.info(
        "Business analysis controls are disabled for viewers. "
        "Existing authorized results may be accessed through permitted "
        "read-only report views."
    )


# ---------------------------------------------------------
# 11. AI insights
# ---------------------------------------------------------

st.subheader("7. AI insights")

if analysis_result is not None and can_edit:
    try:
        # Prevent viewers from generating or regenerating insights.
        require_editor_access()

        render_insight_dashboard(
            analysis_result,
            workspace_key=INSIGHTS_KEY,
        )

    except WorkspacePermissionError:
        st.warning("Owner or editor permission is required for AI insights.")

elif analysis_result is None:
    st.info("Run business analysis before generating AI insights.")

else:
    st.info(
        "Insight generation and regeneration are restricted to owners "
        "and editors."
    )

insight_report = st.session_state.get(
    f"{INSIGHTS_KEY}_insight_report"
)


# ---------------------------------------------------------
# 12. Reports
# ---------------------------------------------------------

st.subheader("8. Reports")

# Reports are namespaced by the verified user/workspace namespace.
# Active membership is required; viewers may access permitted reports.
try:
    workspace = access.get_accessible_workspace(
        authenticated_user_id=authenticated_user_id,
        workspace_id=selected_workspace_id,
    )

    validate_dataframe_size(original_dataframe)
    validate_dataframe_size(cleaned_dataframe)

    render_reporting_dashboard(
        original_dataframe=original_dataframe,
        cleaned_dataframe=cleaned_dataframe,
        quality_report=None,
        quality_comparison=quality_comparison,
        cleaning_audit=cleaning_audit,
        analysis_result=analysis_result,
        insight_report=insight_report,
        workspace_key=workspace_key,
    )

except Exception:
    logger.exception("Workspace report access failed.")
    st.error(
        "Reports could not be loaded because workspace access "
        "or report validation failed."
    )

report_artifacts = st.session_state.get(
    f"{WORKSPACE_KEY}_report_artifacts"
)


# ---------------------------------------------------------
# 13. Workflow status
# ---------------------------------------------------------

workflow_state = get_workflow_state()

synchronize_workflow_state(
    workflow_state,
    dataset_loaded=True,
    quality_rendered=True,
    cleaning_applied=bool(cleaning_audit),
    analysis_result=analysis_result,
    insight_report=insight_report,
    report_artifacts=report_artifacts,
)

st.divider()
st.subheader("9. Workflow status")

status_rows = stage_summary(workflow_state)

status_labels = {
    "completed": "✅ Completed",
    "pending": "⏳ Pending",
    "running": "🔄 Running",
    "failed": "❌ Failed",
    "skipped": "⏭️ Skipped",
}

for row in status_rows:
    label = status_labels.get(row["status"], row["status"])

    with st.container(border=True):
        left, right = st.columns([2, 3])

        left.markdown(f"**{row['stage']}**")
        right.write(label)

        if row["message"]:
            st.caption(row["message"])

with st.expander("Workflow state (diagnostics)"):
    st.json(workflow_state.to_dict())

# Close the workspace database session after normal dashboard completion.
db_session.close()
