"""Tests for workspace membership and ownership checks."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from business_analyst.workspaces.access import (
    WorkspaceAccessService,
    WorkspaceNotFoundError,
    WorkspacePermissionError,
)
from business_analyst.workspaces.models import (
    DatasetRecord,
    WorkspaceBase,
    WorkspaceRole,
)

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    WorkspaceBase.metadata.create_all(engine)

    with Session(engine) as db_session:
        yield db_session

    engine.dispose()


def test_creator_becomes_workspace_owner(session) -> None:
    access = WorkspaceAccessService(session)

    workspace = access.create_workspace(
        authenticated_user_id="user-a",
        name="Retail workspace",
    )

    retrieved = access.get_accessible_workspace(
        authenticated_user_id="user-a",
        workspace_id=workspace.id,
    )

    assert retrieved.id == workspace.id
    assert retrieved.created_by_user_id == "user-a"


def test_other_user_cannot_access_private_workspace(session) -> None:
    access = WorkspaceAccessService(session)
    workspace = access.create_workspace(
        authenticated_user_id="user-a",
        name="Private workspace",
    )

    with pytest.raises(WorkspaceNotFoundError):
        access.get_accessible_workspace(
            authenticated_user_id="user-b",
            workspace_id=workspace.id,
        )


def test_only_owner_can_add_member(session) -> None:
    access = WorkspaceAccessService(session)
    workspace = access.create_workspace(
        authenticated_user_id="owner",
        name="Team workspace",
    )

    access.add_member(
        authenticated_user_id="owner",
        workspace_id=workspace.id,
        new_user_id="viewer",
        role=WorkspaceRole.VIEWER,
    )

    with pytest.raises(WorkspacePermissionError):
        access.add_member(
            authenticated_user_id="viewer",
            workspace_id=workspace.id,
            new_user_id="another-user",
            role=WorkspaceRole.EDITOR,
        )


def test_editor_can_access_workspace(session) -> None:
    access = WorkspaceAccessService(session)
    workspace = access.create_workspace(
        authenticated_user_id="owner",
        name="Shared workspace",
    )
    access.add_member(
        authenticated_user_id="owner",
        workspace_id=workspace.id,
        new_user_id="editor",
        role=WorkspaceRole.EDITOR,
    )

    retrieved = access.require_role(
        authenticated_user_id="editor",
        workspace_id=workspace.id,
        allowed_roles={
            WorkspaceRole.OWNER,
            WorkspaceRole.EDITOR,
        },
    )

    assert retrieved.id == workspace.id


def test_blank_identity_is_rejected(session) -> None:
    access = WorkspaceAccessService(session)

    with pytest.raises(ValueError):
        access.create_workspace(
            authenticated_user_id=" ",
            name="Invalid workspace",
        )


def test_empty_workspace_name_is_rejected(session) -> None:
    access = WorkspaceAccessService(session)

    with pytest.raises(ValueError):
        access.create_workspace(
            authenticated_user_id="user-a",
            name="  ",
        )
def test_inactive_workspace_cannot_be_accessed(session) -> None:
    access = WorkspaceAccessService(session)

    workspace = access.create_workspace(
        authenticated_user_id="user-a",
        name="Inactive workspace",
    )

    workspace.is_active = False
    session.flush()

    with pytest.raises(WorkspaceNotFoundError):
        access.get_accessible_workspace(
            authenticated_user_id="user-a",
            workspace_id=workspace.id,
        )


def test_viewer_cannot_perform_editor_or_owner_actions(session) -> None:
    access = WorkspaceAccessService(session)

    workspace = access.create_workspace(
        authenticated_user_id="owner",
        name="Read-only workspace",
    )

    access.add_member(
        authenticated_user_id="owner",
        workspace_id=workspace.id,
        new_user_id="viewer",
        role=WorkspaceRole.VIEWER,
    )

    with pytest.raises(WorkspacePermissionError):
        access.require_role(
            authenticated_user_id="viewer",
            workspace_id=workspace.id,
            allowed_roles={
                WorkspaceRole.OWNER,
                WorkspaceRole.EDITOR,
            },
        )


def test_user_cannot_fetch_dataset_from_another_workspace(session) -> None:
    access = WorkspaceAccessService(session)

    workspace_a = access.create_workspace(
        authenticated_user_id="user-a",
        name="Workspace A",
    )

    workspace_b = access.create_workspace(
        authenticated_user_id="user-b",
        name="Workspace B",
    )

    dataset = DatasetRecord(
        workspace_id=workspace_a.id,
        created_by_user_id="user-a",
        filename="sales.csv",
        file_format="csv",
        row_count=3,
        column_count=2,
        content_fingerprint="a" * 64,
    )

    session.add(dataset)
    session.flush()

    with pytest.raises(WorkspaceNotFoundError):
        access.get_dataset(
            authenticated_user_id="user-b",
            workspace_id=workspace_b.id,
            dataset_id=dataset.id,
        )