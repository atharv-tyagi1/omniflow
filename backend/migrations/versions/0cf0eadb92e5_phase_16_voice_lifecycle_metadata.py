"""phase_16_voice_lifecycle_metadata

Revision ID: 0cf0eadb92e5
Revises: ac315f820248
Create Date: 2026-06-16 16:14:38.359105

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0cf0eadb92e5'
down_revision: Union[str, Sequence[str], None] = 'ac315f820248'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("voice_interactions") as batch_op:
        batch_op.add_column(sa.Column("artifact_created_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("artifact_expires_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("artifact_deleted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("voice_interactions") as batch_op:
        batch_op.drop_column("artifact_deleted_at")
        batch_op.drop_column("artifact_expires_at")
        batch_op.drop_column("artifact_created_at")
