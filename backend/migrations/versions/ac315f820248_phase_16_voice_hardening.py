"""phase_16_voice_hardening

Revision ID: ac315f820248
Revises: 0g9l3n04m2e68
Create Date: 2026-06-16 15:52:34.495096

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac315f820248'
down_revision: Union[str, Sequence[str], None] = '0g9l3n04m2e68'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Empty existing table to avoid null constraint issues during migration
    op.execute("DELETE FROM voice_interactions")
    
    with op.batch_alter_table("voice_interactions") as batch_op:
        batch_op.add_column(sa.Column("workspace_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False))
        batch_op.add_column(sa.Column("customer_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
        batch_op.add_column(sa.Column("idempotency_key", sa.String(255), nullable=False))
        batch_op.add_column(sa.Column("channel", sa.String(50), nullable=False, server_default="public_voice"))
        batch_op.add_column(sa.Column("input_audio_ref", sa.String(1024), nullable=True))
        batch_op.add_column(sa.Column("input_audio_sha256", sa.String(64), nullable=True))
        batch_op.add_column(sa.Column("input_audio_mime_type", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("input_audio_size_bytes", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("input_audio_bytes", sa.LargeBinary(), nullable=True))
        batch_op.add_column(sa.Column("transcript_text", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("reply_text", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("reply_audio_ref", sa.String(1024), nullable=True))
        batch_op.add_column(sa.Column("reply_audio_bytes", sa.LargeBinary(), nullable=True))
        batch_op.add_column(sa.Column("status", sa.String(50), nullable=False, server_default="processing"))
        batch_op.add_column(sa.Column("error_code", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("error_message", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
        
        batch_op.create_foreign_key("fk_voice_workspace_id", "workspaces", ["workspace_id"], ["id"], ondelete="CASCADE")
        batch_op.create_foreign_key("fk_voice_customer_id", "customers", ["customer_id"], ["id"], ondelete="SET NULL")
        
        batch_op.create_index("idx_voice_workspace", ["workspace_id"])
        batch_op.create_index("idx_voice_created_at", ["created_at"])
        
        batch_op.create_unique_constraint("uix_workspace_voice_idemp_key", ["workspace_id", "idempotency_key"])
        
        batch_op.alter_column("conversation_id", existing_type=sa.dialects.postgresql.UUID(as_uuid=True), nullable=True)
        batch_op.drop_column("audio_url")
        batch_op.drop_column("transcript")
        batch_op.drop_column("duration_seconds")

def downgrade() -> None:
    with op.batch_alter_table("voice_interactions") as batch_op:
        batch_op.add_column(sa.Column("audio_url", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("transcript", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("duration_seconds", sa.Integer(), nullable=True))
        
        batch_op.alter_column("conversation_id", existing_type=sa.dialects.postgresql.UUID(as_uuid=True), nullable=False)
        
        batch_op.drop_constraint("uix_workspace_voice_idemp_key", type_="unique")
        batch_op.drop_index("idx_voice_created_at")
        batch_op.drop_index("idx_voice_workspace")
        
        batch_op.drop_constraint("fk_voice_customer_id", type_="foreignkey")
        batch_op.drop_constraint("fk_voice_workspace_id", type_="foreignkey")
        
        batch_op.drop_column("updated_at")
        batch_op.drop_column("error_message")
        batch_op.drop_column("error_code")
        batch_op.drop_column("status")
        batch_op.drop_column("reply_audio_bytes")
        batch_op.drop_column("reply_audio_ref")
        batch_op.drop_column("reply_text")
        batch_op.drop_column("transcript_text")
        batch_op.drop_column("input_audio_bytes")
        batch_op.drop_column("input_audio_size_bytes")
        batch_op.drop_column("input_audio_mime_type")
        batch_op.drop_column("input_audio_sha256")
        batch_op.drop_column("input_audio_ref")
        batch_op.drop_column("channel")
        batch_op.drop_column("idempotency_key")
        batch_op.drop_column("customer_id")
        batch_op.drop_column("workspace_id")
