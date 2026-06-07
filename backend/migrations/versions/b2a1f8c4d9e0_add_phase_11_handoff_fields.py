"""add_phase_11_handoff_fields

Revision ID: b2a1f8c4d9e0
Revises: g9l3n04m2e67_cc_lineage_fields  # Ensure this points to the actual latest revision
Create Date: 2026-06-06 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = 'b2a1f8c4d9e0'
down_revision: Union[str, Sequence[str], None] = 'g9l3n04m2e67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # We use batch_alter_table for SQLite compatibility when adding constraints or multiple columns
    bind = op.get_bind()
    
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('previous_agent', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('handoff_count', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('last_handoff_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('last_handoff_reason', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('current_state_version', sa.Integer(), server_default='1', nullable=False))
        
        if bind.dialect.name == "postgresql":
            batch_op.add_column(sa.Column('current_state', JSONB(astext_type=sa.Text()), nullable=True))
        else:
            batch_op.add_column(sa.Column('current_state', sa.JSON(), nullable=True))
            
        batch_op.add_column(sa.Column('unresolved_intent', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('loop_cooldown_until', sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table('handoffs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('workspace_id', UUID(as_uuid=True), nullable=True))
        batch_op.add_column(sa.Column('confidence', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('trigger_intent', sa.String(length=50), nullable=True))
        
        if bind.dialect.name == "postgresql":
            batch_op.add_column(sa.Column('previous_state', JSONB(astext_type=sa.Text()), nullable=True))
            batch_op.add_column(sa.Column('next_state', JSONB(astext_type=sa.Text()), nullable=True))
        else:
            batch_op.add_column(sa.Column('previous_state', sa.JSON(), nullable=True))
            batch_op.add_column(sa.Column('next_state', sa.JSON(), nullable=True))
            
        batch_op.add_column(sa.Column('status', sa.String(length=20), server_default='completed', nullable=False))
        batch_op.add_column(sa.Column('source_message_id', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('source_entity_type', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('source_entity_id', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('target_entity_type', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('target_entity_id', sa.String(length=255), nullable=True))
        
        batch_op.create_foreign_key('fk_handoffs_workspace_id', 'workspaces', ['workspace_id'], ['id'], ondelete='CASCADE')
        batch_op.create_unique_constraint('uq_handoff_source_message', ['workspace_id', 'conversation_id', 'source_message_id'])

def downgrade() -> None:
    bind = op.get_bind()
    with op.batch_alter_table('handoffs', schema=None) as batch_op:
        batch_op.drop_constraint('uq_handoff_source_message', type_='unique')
        batch_op.drop_constraint('fk_handoffs_workspace_id', type_='foreignkey')
        batch_op.drop_column('target_entity_id')
        batch_op.drop_column('target_entity_type')
        batch_op.drop_column('source_entity_id')
        batch_op.drop_column('source_entity_type')
        batch_op.drop_column('source_message_id')
        batch_op.drop_column('status')
        batch_op.drop_column('next_state')
        batch_op.drop_column('previous_state')
        batch_op.drop_column('trigger_intent')
        batch_op.drop_column('confidence')
        batch_op.drop_column('workspace_id')

    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.drop_column('loop_cooldown_until')
        batch_op.drop_column('unresolved_intent')
        batch_op.drop_column('current_state')
        batch_op.drop_column('current_state_version')
        batch_op.drop_column('last_handoff_reason')
        batch_op.drop_column('last_handoff_at')
        batch_op.drop_column('handoff_count')
        batch_op.drop_column('previous_agent')
