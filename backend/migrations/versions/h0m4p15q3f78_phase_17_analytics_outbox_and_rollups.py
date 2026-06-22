"""phase_17_analytics_outbox_and_rollups

Revision ID: h0m4p15q3f78
Revises: 0cf0eadb92e5
Create Date: 2026-06-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'h0m4p15q3f78'
down_revision = '0cf0eadb92e5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # analytics_outbox — durable transactional outbox
    op.create_table(
        'analytics_outbox',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(80), nullable=False),
        sa.Column('source_agent', sa.String(50), nullable=True),
        sa.Column('target_agent', sa.String(50), nullable=True),
        sa.Column('event_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('idempotency_key', sa.String(255), nullable=True),
        sa.Column('schema_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_outbox_idempotency_key', 'analytics_outbox', ['idempotency_key'])
    op.create_index('ix_outbox_status_created', 'analytics_outbox', ['status', 'created_at'])

    # analytics_events — canonical event store
    op.create_table(
        'analytics_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(80), nullable=False),
        sa.Column('source_agent', sa.String(50), nullable=True),
        sa.Column('target_agent', sa.String(50), nullable=True),
        sa.Column('event_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('idempotency_key', sa.String(255), nullable=True, unique=True),
        sa.Column('schema_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
    )
    op.create_index('ix_analytics_events_workspace_id', 'analytics_events', ['workspace_id'])
    op.create_index('ix_analytics_events_conversation_id', 'analytics_events', ['conversation_id'])
    op.create_index('ix_analytics_events_customer_id', 'analytics_events', ['customer_id'])
    op.create_index('ix_analytics_events_event_type', 'analytics_events', ['event_type'])
    op.create_index('ix_analytics_events_created_at', 'analytics_events', ['created_at'])
    op.create_index('ix_analytics_events_idempotency_key', 'analytics_events', ['idempotency_key'])
    op.create_index('ix_analytics_events_ws_type_date', 'analytics_events',
                    ['workspace_id', 'event_type', 'created_at'])

    # analytics_hourly_rollups
    op.create_table(
        'analytics_hourly_rollups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('time_bucket', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metric_name', sa.String(80), nullable=False),
        sa.Column('dimension', postgresql.JSONB(), nullable=True),
        sa.Column('value', sa.Numeric(14, 4), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
    )
    op.create_index('ix_hr_ws_bucket_metric', 'analytics_hourly_rollups',
                    ['workspace_id', 'time_bucket', 'metric_name'])

    # analytics_daily_rollups
    op.create_table(
        'analytics_daily_rollups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('time_bucket', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metric_name', sa.String(80), nullable=False),
        sa.Column('dimension', postgresql.JSONB(), nullable=True),
        sa.Column('value', sa.Numeric(14, 4), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
    )
    op.create_index('ix_dr_ws_bucket_metric', 'analytics_daily_rollups',
                    ['workspace_id', 'time_bucket', 'metric_name'])


def downgrade() -> None:
    op.drop_table('analytics_daily_rollups')
    op.drop_table('analytics_hourly_rollups')
    op.drop_table('analytics_events')
    op.drop_table('analytics_outbox')
