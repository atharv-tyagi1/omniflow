"""create customer_care_cases

Revision ID: e7j1k82l0c45
Revises: 7bb7ab628663
Create Date: 2026-06-06 07:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e7j1k82l0c45'
down_revision = '7bb7ab628663'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create customer_care_cases table
    op.create_table(
        'customer_care_cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('complaint_type', sa.String(length=50), nullable=True),
        sa.Column('refund_requested', sa.Boolean(), nullable=True),
        sa.Column('refund_amount_requested', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('order_id', sa.String(length=100), nullable=True),
        sa.Column('account_issue_type', sa.String(length=100), nullable=True),
        sa.Column('sentiment', sa.String(length=20), nullable=True),
        sa.Column('current_stage', sa.String(length=50), nullable=False, server_default='acknowledged'),
        sa.Column('escalation_reason', sa.Text(), nullable=True),
        sa.Column('resolution_timeline', sa.String(length=255), nullable=True),
        sa.Column('last_interaction_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_cc_cases_workspace', 'customer_care_cases', ['workspace_id'], unique=False)
    op.create_index('idx_cc_cases_ws_conv', 'customer_care_cases', ['workspace_id', 'conversation_id'], unique=False)
    op.create_index('idx_cc_cases_ws_stage', 'customer_care_cases', ['workspace_id', 'current_stage'], unique=False)

def downgrade() -> None:
    op.drop_index('idx_cc_cases_ws_stage', table_name='customer_care_cases')
    op.drop_index('idx_cc_cases_ws_conv', table_name='customer_care_cases')
    op.drop_index('idx_cc_cases_workspace', table_name='customer_care_cases')
    op.drop_table('customer_care_cases')
