"""Phase 13.5: Public OmniFlow API Layer

Revision ID: 06f4454daa4a
Revises: 5fc9375aba04
Create Date: 2026-06-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '06f4454daa4a'
down_revision = '5fc9375aba04'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Add external_id to customers
    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('external_id', sa.String(length=255), nullable=True))
        batch_op.create_unique_constraint('uq_workspace_customer_external_id', ['workspace_id', 'external_id'])
    op.create_index('idx_customers_external', 'customers', ['external_id'], unique=False)

    # 2. Add external_id to conversations
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('external_id', sa.String(length=255), nullable=True))
        batch_op.create_unique_constraint('uq_workspace_conversation_external_id', ['workspace_id', 'external_id'])
    op.create_index('idx_conversations_external', 'conversations', ['external_id'], unique=False)

    # 3. Create public_api_keys
    op.create_table('public_api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('key_hash', sa.String(), nullable=False),
        sa.Column('prefix', sa.String(length=8), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_public_api_keys_prefix', 'public_api_keys', ['prefix'], unique=False)
    op.create_index('ix_public_api_keys_workspace_id', 'public_api_keys', ['workspace_id'], unique=False)

    # 4. Create public_api_key_scopes
    op.create_table('public_api_key_scopes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('api_key_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scope_name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['api_key_id'], ['public_api_keys.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('api_key_id', 'scope_name', name='uq_public_api_key_scope')
    )
    op.create_index('ix_public_api_key_scopes_key_id', 'public_api_key_scopes', ['api_key_id'], unique=False)

    # 5. Create public_api_key_rotations
    op.create_table('public_api_key_rotations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('api_key_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('old_key_prefix', sa.String(length=8), nullable=False),
        sa.Column('new_key_prefix', sa.String(length=8), nullable=False),
        sa.Column('rotated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rotated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['api_key_id'], ['public_api_keys.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rotated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_public_api_key_rotations_api_key_id', 'public_api_key_rotations', ['api_key_id'], unique=False)
    op.create_index('ix_public_api_key_rotations_workspace_id', 'public_api_key_rotations', ['workspace_id'], unique=False)

    # 6. Create idempotency_keys
    op.create_table('idempotency_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('idempotency_key', sa.String(), nullable=False),
        sa.Column('path', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('response_body', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'idempotency_key', name='uq_workspace_idempotency_key')
    )
    op.create_index('ix_idempotency_keys_expires_at', 'idempotency_keys', ['expires_at'], unique=False)

    # 7. Create public_webhooks
    op.create_table('public_webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('secret_hash', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'source', name='uq_workspace_webhook_source')
    )

    # 8. Create public_async_jobs
    op.create_table('public_async_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('result_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_public_async_jobs_workspace_id_status', 'public_async_jobs', ['workspace_id', 'status'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_public_async_jobs_workspace_id_status', table_name='public_async_jobs')
    op.drop_table('public_async_jobs')
    op.drop_table('public_webhooks')
    op.drop_index('ix_idempotency_keys_expires_at', table_name='idempotency_keys')
    op.drop_table('idempotency_keys')
    op.drop_index('ix_public_api_key_rotations_workspace_id', table_name='public_api_key_rotations')
    op.drop_index('ix_public_api_key_rotations_api_key_id', table_name='public_api_key_rotations')
    op.drop_table('public_api_key_rotations')
    op.drop_index('ix_public_api_key_scopes_key_id', table_name='public_api_key_scopes')
    op.drop_table('public_api_key_scopes')
    op.drop_index('ix_public_api_keys_workspace_id', table_name='public_api_keys')
    op.drop_index('ix_public_api_keys_prefix', table_name='public_api_keys')
    op.drop_table('public_api_keys')
    op.drop_index('idx_conversations_external', table_name='conversations')
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.drop_constraint('uq_workspace_conversation_external_id', type_='unique')
        batch_op.drop_column('external_id')
    op.drop_index('idx_customers_external', table_name='customers')
    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.drop_constraint('uq_workspace_customer_external_id', type_='unique')
        batch_op.drop_column('external_id')
