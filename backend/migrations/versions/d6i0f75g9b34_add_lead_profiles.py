"""Add LeadProfile

Revision ID: d6i0f75g9b34
Revises: c5h9e64f8a23
Create Date: 2026-06-05 16:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd6i0f75g9b34'
down_revision: Union[str, None] = 'c5h9e64f8a23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('lead_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_size', sa.String(length=100), nullable=True),
        sa.Column('budget', sa.String(length=100), nullable=True),
        sa.Column('urgency', sa.String(length=100), nullable=True),
        sa.Column('use_case', sa.String(length=500), nullable=True),
        sa.Column('buying_intent', sa.Enum('low', 'medium', 'high', name='buyingintent'), nullable=True),
        sa.Column('current_stage', sa.Enum('new', 'discovery', 'qualified', 'objection', 'ready_to_buy', 'converted', 'lost', name='salesfunnelstage'), nullable=False),
        sa.Column('objections', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('lead_score', sa.Integer(), nullable=True),
        sa.Column('last_interaction_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_stage_change_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_channel', sa.String(length=100), nullable=True),
        sa.Column('next_best_action', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'customer_id', name='uq_lead_workspace_customer')
    )
    op.create_index('idx_leads_workspace_interaction', 'lead_profiles', ['workspace_id', 'last_interaction_at'], unique=False)
    op.create_index('idx_leads_workspace_intent', 'lead_profiles', ['workspace_id', 'buying_intent'], unique=False)
    op.create_index('idx_leads_workspace_stage', 'lead_profiles', ['workspace_id', 'current_stage'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_leads_workspace_stage', table_name='lead_profiles')
    op.drop_index('idx_leads_workspace_intent', table_name='lead_profiles')
    op.drop_index('idx_leads_workspace_interaction', table_name='lead_profiles')
    op.drop_table('lead_profiles')
    op.execute("DROP TYPE buyingintent")
    op.execute("DROP TYPE salesfunnelstage")
