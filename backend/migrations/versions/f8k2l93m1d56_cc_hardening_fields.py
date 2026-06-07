"""cc hardening fields

Revision ID: f8k2l93m1d56
Revises: e7j1k82l0c45
Create Date: 2026-06-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f8k2l93m1d56'
down_revision = 'e7j1k82l0c45'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Phase 11 tracking fields
    op.add_column('customer_care_cases', sa.Column('handoff_recommended', sa.Boolean(), nullable=True, server_default=sa.text('false')))
    op.add_column('customer_care_cases', sa.Column('next_agent', sa.String(length=50), nullable=True))
    op.add_column('customer_care_cases', sa.Column('source_agent', sa.String(length=50), nullable=True))

    # Drop old non-composite indexes
    op.drop_index('idx_cc_cases_ws_conv', table_name='customer_care_cases')
    op.drop_index('idx_cc_cases_ws_stage', table_name='customer_care_cases')

    # Add new composite and partial active indexes
    op.create_index('idx_cc_cases_ws_conv_stage', 'customer_care_cases', ['workspace_id', 'conversation_id', 'current_stage'], unique=False)
    op.create_index('idx_cc_cases_ws_interaction', 'customer_care_cases', ['workspace_id', 'last_interaction_at'], unique=False)
    op.create_index('idx_cc_cases_ws_complaint', 'customer_care_cases', ['workspace_id', 'complaint_type'], unique=False)

    # Concurrency guard: Only one active case per workspace/conversation
    # Uses sqlite_where for sqlite tests and postgresql_where for production
    op.create_index(
        'idx_cc_cases_unique_active',
        'customer_care_cases',
        ['workspace_id', 'conversation_id'],
        unique=True,
        postgresql_where=sa.text("current_stage NOT IN ('resolved', 'closed')"),
        sqlite_where=sa.text("current_stage NOT IN ('resolved', 'closed')")
    )


def downgrade() -> None:
    op.drop_index('idx_cc_cases_unique_active', table_name='customer_care_cases')
    op.drop_index('idx_cc_cases_ws_complaint', table_name='customer_care_cases')
    op.drop_index('idx_cc_cases_ws_interaction', table_name='customer_care_cases')
    op.drop_index('idx_cc_cases_ws_conv_stage', table_name='customer_care_cases')
    
    op.create_index('idx_cc_cases_ws_stage', 'customer_care_cases', ['workspace_id', 'current_stage'], unique=False)
    op.create_index('idx_cc_cases_ws_conv', 'customer_care_cases', ['workspace_id', 'conversation_id'], unique=False)
    
    op.drop_column('customer_care_cases', 'source_agent')
    op.drop_column('customer_care_cases', 'next_agent')
    op.drop_column('customer_care_cases', 'handoff_recommended')
