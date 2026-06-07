"""create_workspaces_and_users_tables

Revision ID: 8d9d412d6fcb
Revises:
Create Date: 2026-06-02 14:03:15.106885

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8d9d412d6fcb"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create workspaces table
    op.create_table(
        "workspaces",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("plan", sa.String(length=50), server_default="free", nullable=False),
        sa.Column(
            "status", sa.String(length=20), server_default="active", nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_workspaces_status", "workspaces", ["status"], unique=False)

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column(
            "role", sa.String(length=50), server_default="member", nullable=False
        ),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column(
            "status", sa.String(length=20), server_default="active", nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], name="users_workspace_id_fkey", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("idx_users_workspace", "users", ["workspace_id"], unique=False)
    op.create_index("idx_users_email", "users", ["email"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_users_email", table_name="users")
    op.drop_index("idx_users_workspace", table_name="users")
    op.drop_table("users")
    op.drop_index("idx_workspaces_status", table_name="workspaces")
    op.drop_table("workspaces")
