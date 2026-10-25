"""Workspace membership and authorization checks."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from business_analyst.workspaces.models import (
    DatasetRecord,
    Workspace,
    WorkspaceMembership,
    WorkspaceRole,
)


class WorkspaceAccessError(Exception):
    """Base exception for workspace access failures."""


class WorkspaceNotFoundError(WorkspaceAccessError):
    """Raised when a workspace is missing or inaccessible."""


class WorkspacePermissionError(WorkspaceAccessError):
    """Raised when a user lacks permission for an action."""


def validate_workspace_role(role: WorkspaceRole | str) -> WorkspaceRole:
    """Reject unknown roles rather than silently accepting them."""
    try:
        return WorkspaceRole(role)
    except (ValueError, TypeError) as exc:
        raise WorkspacePermissionError("Invalid workspace role.") from exc


class WorkspaceAccessService:
    """Authorize workspace operations using verified user identities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_workspace(
        self,
        *,
        authenticated_user_id: str,
        name: str,
    ) -> Workspace:
        """Create a workspace and grant its creator the owner role."""
        user_id = self._require_user_id(authenticated_user_id)
        clean_name = name.strip()

        if not clean_name:
            raise ValueError("Workspace name cannot be empty.")
        if len(clean_name) > 120:
            raise ValueError("Workspace name cannot exceed 120 characters.")

        workspace = Workspace(
            name=clean_name,
            created_by_user_id=user_id,
            is_active=True,
        )
        self.session.add(workspace)
        self.session.flush()

        membership = WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=user_id,
            role=WorkspaceRole.OWNER.value,
        )
        self.session.add(membership)
        self.session.flush()

        return workspace

    def get_accessible_workspace(
        self,
        *,
        authenticated_user_id: str,
        workspace_id: str,
    ) -> Workspace:
        """Return a workspace only if the user is an active member."""
        user_id = self._require_user_id(authenticated_user_id)

        statement = (
            select(Workspace)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == Workspace.id,
            )
            .where(
                Workspace.id == workspace_id,
                WorkspaceMembership.user_id == user_id,
                Workspace.is_active.is_(True),
            )
        )
        workspace = self.session.scalar(statement)

        # Do not disclose whether an inaccessible workspace exists.
        if workspace is None:
            raise WorkspaceNotFoundError("Workspace not found or access denied.")

        return workspace

    def require_role(
        self,
        *,
        authenticated_user_id: str,
        workspace_id: str,
        allowed_roles: set[WorkspaceRole],
    ) -> Workspace:
        """Check workspace membership and the required role."""
        workspace = self.get_accessible_workspace(
            authenticated_user_id=authenticated_user_id,
            workspace_id=workspace_id,
        )

        membership_statement = select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == self._require_user_id(authenticated_user_id),
        )
        membership = self.session.scalar(membership_statement)

        if membership is None or membership.role not in {
            role.value for role in allowed_roles
        }:
            raise WorkspacePermissionError(
                "You do not have permission to perform this action."
            )

        return workspace

    def add_member(
        self,
        *,
        authenticated_user_id: str,
        workspace_id: str,
        new_user_id: str,
        role: WorkspaceRole | str,
    ) -> WorkspaceMembership:
        """Allow only an owner to add a member or change access."""
        validated_role = validate_workspace_role(role)

        self.require_role(
            authenticated_user_id=authenticated_user_id,
            workspace_id=workspace_id,
            allowed_roles={WorkspaceRole.OWNER},
        )

        user_id = self._require_user_id(new_user_id)

        if validated_role == WorkspaceRole.OWNER:
            raise ValueError(
                "Use a separate, audited ownership-transfer operation "
                "to grant the owner role."
            )

        statement = select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user_id,
        )
        membership = self.session.scalar(statement)

        if membership is None:
            membership = WorkspaceMembership(
                workspace_id=workspace_id,
                user_id=user_id,
                role=validated_role.value,
            )
            self.session.add(membership)
        else:
            membership.role = validated_role.value

        self.session.flush()
        return membership

    def get_dataset(
        self,
        *,
        authenticated_user_id: str,
        workspace_id: str,
        dataset_id: str,
    ) -> DatasetRecord:
        """Fetch dataset metadata only within an authorized workspace."""
        self.get_accessible_workspace(
            authenticated_user_id=authenticated_user_id,
            workspace_id=workspace_id,
        )

        statement = select(DatasetRecord).where(
            DatasetRecord.id == dataset_id,
            DatasetRecord.workspace_id == workspace_id,
            DatasetRecord.is_deleted.is_(False),
        )
        record = self.session.scalar(statement)

        if record is None:
            raise WorkspaceNotFoundError("Dataset not found in this workspace.")

        return record

    @staticmethod
    def _require_user_id(user_id: str) -> str:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("A verified authenticated user ID is required.")

        return user_id.strip()
