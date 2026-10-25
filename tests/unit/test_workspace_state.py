"""Tests for workspace-scoped state keys."""

import pytest

from business_analyst.workspaces.state import (
    clear_workspace_artifacts,
    clear_workspace_downstream,
    workspace_namespace,
    workspace_state_key,
)


def test_different_users_get_different_namespaces() -> None:
    first = workspace_namespace(
        authenticated_user_id="user-a",
        workspace_id="workspace-1",
    )
    second = workspace_namespace(
        authenticated_user_id="user-b",
        workspace_id="workspace-1",
    )
    assert first != second


def test_different_workspaces_get_different_namespaces() -> None:
    first = workspace_namespace(
        authenticated_user_id="user-a",
        workspace_id="workspace-1",
    )
    second = workspace_namespace(
        authenticated_user_id="user-a",
        workspace_id="workspace-2",
    )
    assert first != second


def test_key_is_stable_for_same_identity() -> None:
    first = workspace_state_key(
        authenticated_user_id="user-a",
        workspace_id="workspace-1",
        artifact="analysis_result",
    )
    second = workspace_state_key(
        authenticated_user_id="user-a",
        workspace_id="workspace-1",
        artifact="analysis_result",
    )
    assert first == second


def test_invalid_artifact_name_is_rejected() -> None:
    with pytest.raises(ValueError):
        workspace_state_key(
            authenticated_user_id="user-a",
            workspace_id="workspace-1",
            artifact="analysis-result!",
        )


def test_clear_workspace_does_not_clear_another_workspace() -> None:
    state = {}
    key_a = workspace_state_key(
        authenticated_user_id="user-a",
        workspace_id="workspace-1",
        artifact="analysis_result",
    )
    key_b = workspace_state_key(
        authenticated_user_id="user-a",
        workspace_id="workspace-2",
        artifact="analysis_result",
    )
    state[key_a] = {"secret": "workspace A"}
    state[key_b] = {"secret": "workspace B"}

    clear_workspace_artifacts(
        state,
        authenticated_user_id="user-a",
        workspace_id="workspace-1",
    )

    assert key_a not in state
    assert state[key_b] == {"secret": "workspace B"}


def test_clear_downstream_preserves_dataset_data() -> None:
    state = {}
    cleaned_key = workspace_state_key(
        authenticated_user_id="user-a",
        workspace_id="workspace-1",
        artifact="cleaned",
    )
    analysis_key = workspace_state_key(
        authenticated_user_id="user-a",
        workspace_id="workspace-1",
        artifact="analysis_result",
    )
    state[cleaned_key] = "cleaned-data"
    state[analysis_key] = "old-analysis"

    clear_workspace_downstream(
        state,
        authenticated_user_id="user-a",
        workspace_id="workspace-1",
    )

    assert state[cleaned_key] == "cleaned-data"
    assert analysis_key not in state
