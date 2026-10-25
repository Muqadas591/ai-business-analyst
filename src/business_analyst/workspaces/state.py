"""Workspace-scoped Streamlit state helpers."""

from __future__ import annotations

import hashlib
import re
from collections.abc import MutableMapping


WORKSPACE_ARTIFACT_NAMES = (
    "ingestion_result",
    "original",
    "cleaned",
    "audit",
    "cleaning_plan",
    "cleaned_fingerprint",
    "quality_report",
    "quality_comparison",
    "analysis_result",
    "insights_analysis_result",
    "insights_insight_report",
    "insights_report",
    "report_artifacts",
    "workflow_state",
)


def workspace_namespace(
    *,
    authenticated_user_id: str,
    workspace_id: str,
) -> str:
    """Create an opaque, stable namespace for one user/workspace pair."""
    if not authenticated_user_id.strip():
        raise ValueError("Authenticated user ID is required.")
    if not workspace_id.strip():
        raise ValueError("Workspace ID is required.")

    identity = f"{authenticated_user_id.strip()}:{workspace_id.strip()}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
    return f"ws_{digest}"


def workspace_state_key(
    *,
    authenticated_user_id: str,
    workspace_id: str,
    artifact: str,
) -> str:
    """Return a session-state key scoped to one user and workspace."""
    if not re.fullmatch(r"[a-z][a-z0-9_]*", artifact):
        raise ValueError("Invalid workspace artifact name.")

    return (
        f"{workspace_namespace(authenticated_user_id=authenticated_user_id, workspace_id=workspace_id)}"
        f"_{artifact}"
    )


def clear_workspace_artifacts(
    session_state: MutableMapping,
    *,
    authenticated_user_id: str,
    workspace_id: str,
) -> None:
    """Clear only artifacts in the specified workspace namespace."""
    namespace = workspace_namespace(
        authenticated_user_id=authenticated_user_id,
        workspace_id=workspace_id,
    )
    prefix = f"{namespace}_"

    for key in list(session_state.keys()):
        if key.startswith(prefix):
            session_state.pop(key, None)


def clear_workspace_downstream(
    session_state: MutableMapping,
    *,
    authenticated_user_id: str,
    workspace_id: str,
    from_artifacts: tuple[str, ...] = (
        "analysis_result",
        "insights_analysis_result",
        "insights_insight_report",
        "insights_report",
        "report_artifacts",
    ),
) -> None:
    """Invalidate selected downstream outputs in one workspace."""
    for artifact in from_artifacts:
        key = workspace_state_key(
            authenticated_user_id=authenticated_user_id,
            workspace_id=workspace_id,
            artifact=artifact,
        )
        session_state.pop(key, None)
