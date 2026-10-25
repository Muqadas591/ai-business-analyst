"""Create application user accounts.

Revision ID: d4c9b7a21f30
Revises: 0a8825e54f25
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "d4c9b7a21f30"
down_revision = "0a8825e54f25"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the application user table."""
    op.create_table(
        "app_users",
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "username",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_app_users_username",
        "app_users",
        ["username"],
        unique=True,
    )


def downgrade() -> None:
    """Remove the application user table."""
    op.drop_index(
        "ix_app_users_username",
        table_name="app_users",
    )
    op.drop_table("app_users")