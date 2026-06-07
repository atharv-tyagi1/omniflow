"""Phase 13.5: Async Job Hardening

Revision ID: 07f4454daa4b
Revises: 06f4454daa4a
Create Date: 2026-06-07 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '07f4454daa4b'
down_revision = '06f4454daa4a'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add new fields to public_async_jobs
    op.add_column('public_async_jobs', sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('public_async_jobs', sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='5'))
    op.add_column('public_async_jobs', sa.Column('last_error', sa.Text(), nullable=True))
    op.add_column('public_async_jobs', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))
    
    op.create_index('ix_public_async_jobs_status_attempts', 'public_async_jobs', ['status', 'attempts'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_public_async_jobs_status_attempts', table_name='public_async_jobs')
    
    op.drop_column('public_async_jobs', 'expires_at')
    op.drop_column('public_async_jobs', 'last_error')
    op.drop_column('public_async_jobs', 'max_attempts')
    op.drop_column('public_async_jobs', 'attempts')
