"""Add support fields to ticket

Revision ID: 7bb7ab628663
Revises: d6i0f75g9b34
Create Date: 2026-06-06 12:02:19.970646

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7bb7ab628663'
down_revision: Union[str, Sequence[str], None] = 'd6i0f75g9b34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new support persistence columns to tickets
    op.add_column("tickets", sa.Column("issue_type", sa.String(length=50), nullable=True))
    op.add_column("tickets", sa.Column("probable_cause", sa.Text(), nullable=True))
    op.add_column("tickets", sa.Column("last_troubleshooting_step", sa.Text(), nullable=True))
    op.add_column("tickets", sa.Column("escalation_reason", sa.Text(), nullable=True))
    op.add_column("tickets", sa.Column("last_interaction_at", sa.DateTime(timezone=True), nullable=True))

    # Add indices
    op.create_index("idx_tickets_ws_issue", "tickets", ["workspace_id", "issue_type"])
    op.create_index("idx_tickets_ws_last_interaction", "tickets", ["workspace_id", "last_interaction_at"])
    op.create_index("idx_tickets_ws_conv_status", "tickets", ["workspace_id", "conversation_id", "status"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indices
    op.drop_index("idx_tickets_ws_conv_status", table_name="tickets")
    op.drop_index("idx_tickets_ws_last_interaction", table_name="tickets")
    op.drop_index("idx_tickets_ws_issue", table_name="tickets")

    # Drop columns
    op.drop_column("tickets", "last_interaction_at")
    op.drop_column("tickets", "escalation_reason")
    op.drop_column("tickets", "last_troubleshooting_step")
    op.drop_column("tickets", "probable_cause")
    op.drop_column("tickets", "issue_type")
