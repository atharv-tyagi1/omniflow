"""phase_14_business_analyst

Revision ID: 0f866a056e47
Revises: 07f4454daa4b
Create Date: 2026-06-07 17:10:20.176830

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f866a056e47'
down_revision: Union[str, Sequence[str], None] = '07f4454daa4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # business_insights
    op.create_table(
        'business_insights',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('confidence_reason', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('evidence_snapshot', sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column('insight_version', sa.Integer(), nullable=False),
        sa.Column('generated_by_engine_version', sa.String(), nullable=False),
        sa.Column('engine_config_version', sa.String(), nullable=False),
        sa.Column('data_freshness_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('snapshot_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('fingerprint', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_business_insight_workspace', 'business_insights', ['workspace_id'], unique=False)
    op.create_index('ix_business_insight_fingerprint', 'business_insights', ['workspace_id', 'fingerprint'], unique=True)
    op.create_index('ix_business_insight_status', 'business_insights', ['status'], unique=False)

    # insight_lineage
    op.create_table(
        'insight_lineage',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('insight_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('source_identifier', sa.String(), nullable=False),
        sa.Column('source_version', sa.String(), nullable=True),
        sa.Column('source_date_range', sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['insight_id'], ['business_insights.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_insight_lineage_insight_id', 'insight_lineage', ['insight_id'], unique=False)

    # business_recommendations
    op.create_table(
        'business_recommendations',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('insight_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recommendation', sa.Text(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('priority', sa.String(), nullable=False),
        sa.Column('recommendation_engine_version', sa.String(), nullable=False),
        sa.Column('recommendation_rule_id', sa.String(), nullable=False),
        sa.Column('effectiveness_status', sa.String(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['insight_id'], ['business_insights.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_business_rec_workspace', 'business_recommendations', ['workspace_id'], unique=False)
    op.create_index('ix_business_rec_insight', 'business_recommendations', ['insight_id'], unique=False)

    # executive_reports
    op.create_table(
        'executive_reports',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_type', sa.String(), nullable=False),
        sa.Column('report_period', sa.String(), nullable=False),
        sa.Column('summary', sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column('report_version', sa.Integer(), nullable=False),
        sa.Column('generated_by_engine_version', sa.String(), nullable=False),
        sa.Column('engine_config_version', sa.String(), nullable=False),
        sa.Column('data_freshness_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('snapshot_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('fingerprint', sa.String(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_executive_report_workspace', 'executive_reports', ['workspace_id'], unique=False)
    op.create_index('ix_executive_report_fingerprint', 'executive_reports', ['workspace_id', 'fingerprint'], unique=True)

    # business_question_audit
    op.create_table(
        'business_question_audit',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('classification', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_question_audit_workspace', 'business_question_audit', ['workspace_id'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_question_audit_workspace', table_name='business_question_audit')
    op.drop_table('business_question_audit')
    
    op.drop_index('ix_executive_report_fingerprint', table_name='executive_reports')
    op.drop_index('ix_executive_report_workspace', table_name='executive_reports')
    op.drop_table('executive_reports')
    
    op.drop_index('ix_business_rec_insight', table_name='business_recommendations')
    op.drop_index('ix_business_rec_workspace', table_name='business_recommendations')
    op.drop_table('business_recommendations')
    
    op.drop_index('ix_insight_lineage_insight_id', table_name='insight_lineage')
    op.drop_table('insight_lineage')
    
    op.drop_index('ix_business_insight_status', table_name='business_insights')
    op.drop_index('ix_business_insight_fingerprint', table_name='business_insights')
    op.drop_index('ix_business_insight_workspace', table_name='business_insights')
    op.drop_table('business_insights')
