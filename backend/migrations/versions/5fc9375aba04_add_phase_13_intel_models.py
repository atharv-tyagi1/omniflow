"""add_phase_13_intel_models

Revision ID: 5fc9375aba04
Revises: b2a1f8c4d9e0
Create Date: 2026-06-06 21:28:44.440776

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5fc9375aba04'
down_revision: Union[str, Sequence[str], None] = 'b2a1f8c4d9e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # JSON type fallback
    JSON_TYPE = sa.JSON().with_variant(sa.dialects.postgresql.JSONB, "postgresql")

    # 1. TopicRegistry
    op.create_table(
        "topic_registry",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("canonical_topic", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("aliases", JSON_TYPE, nullable=False),
        sa.Column("category", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index("idx_topic_registry_canonical", "topic_registry", ["workspace_id", "canonical_topic"], unique=True)

    # 2. ConversationIntelligence
    op.create_table(
        "conversation_intelligence",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("conversation_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("primary_intent", sa.String(255), nullable=True),
        sa.Column("sentiment", sa.String(50), nullable=True),
        sa.Column("resolution", sa.String(50), nullable=True),
        sa.Column("needs_review", sa.Boolean(), nullable=False),
        sa.Column("raw_confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("review_reason", sa.String(255), nullable=True),
        sa.Column("analysis_schema_version", sa.Integer(), nullable=False),
        sa.Column("analyzer_version", sa.String(50), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index("idx_conv_intel_ws_conv", "conversation_intelligence", ["workspace_id", "conversation_id"], unique=True)
    op.create_index("idx_conv_intel_analyzed_at", "conversation_intelligence", ["workspace_id", "analyzed_at"])

    # 3. ConversationIntent
    op.create_table(
        "conversation_intents",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("conversation_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("primary_intent", sa.String(255), nullable=False),
        sa.Column("secondary_intents", JSON_TYPE, nullable=False),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("analysis_schema_version", sa.Integer(), nullable=False),
        sa.Column("analyzer_version", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index("idx_conv_intent_ws_conv", "conversation_intents", ["workspace_id", "conversation_id"], unique=True)

    # 4. ConversationTopic
    op.create_table(
        "conversation_topics",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("conversation_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_name", sa.String(255), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("needs_review", sa.Boolean(), nullable=False),
        sa.Column("analysis_schema_version", sa.Integer(), nullable=False),
        sa.Column("analyzer_version", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index("idx_conv_topics_ws_conv", "conversation_topics", ["workspace_id", "conversation_id"])
    op.create_index("idx_conv_topics_name", "conversation_topics", ["workspace_id", "topic_name"])

    # 5. ConversationSentiment
    op.create_table(
        "conversation_sentiments",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("conversation_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sentiment", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("needs_review", sa.Boolean(), nullable=False),
        sa.Column("analysis_schema_version", sa.Integer(), nullable=False),
        sa.Column("analyzer_version", sa.String(50), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index("idx_conv_sentiment_ws_conv", "conversation_sentiments", ["workspace_id", "conversation_id"], unique=True)

    # 6. ConversationResolution
    op.create_table(
        "conversation_resolutions",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("conversation_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resolution_type", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("needs_review", sa.Boolean(), nullable=False),
        sa.Column("analysis_schema_version", sa.Integer(), nullable=False),
        sa.Column("analyzer_version", sa.String(50), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index("idx_conv_resolution_ws_conv", "conversation_resolutions", ["workspace_id", "conversation_id"], unique=True)

    # 7. ConversationSummary
    op.create_table(
        "conversation_summaries",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("conversation_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("short_summary", sa.Text(), nullable=False),
        sa.Column("long_summary", sa.Text(), nullable=True),
        sa.Column("summary_version", sa.Integer(), nullable=False),
        sa.Column("analysis_schema_version", sa.Integer(), nullable=False),
        sa.Column("analyzer_version", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index("idx_conv_summary_ws_conv", "conversation_summaries", ["workspace_id", "conversation_id"], unique=True)

    # 8. IntelDailyTopicRollup
    op.create_table(
        "intel_daily_topic_rollups",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("time_bucket", sa.DateTime(timezone=True), nullable=False),
        sa.Column("topic_name", sa.String(255), nullable=False),
        sa.Column("value", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index("idx_intel_topic_rollup_ws_bucket_name", "intel_daily_topic_rollups", ["workspace_id", "time_bucket", "topic_name"], unique=True)

    # 9. IntelDailyIntentRollup
    op.create_table(
        "intel_daily_intent_rollups",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("time_bucket", sa.DateTime(timezone=True), nullable=False),
        sa.Column("intent_name", sa.String(255), nullable=False),
        sa.Column("value", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index("idx_intel_intent_rollup_ws_bucket_name", "intel_daily_intent_rollups", ["workspace_id", "time_bucket", "intent_name"], unique=True)

    # 10. IntelDailySentimentRollup
    op.create_table(
        "intel_daily_sentiment_rollups",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("time_bucket", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sentiment", sa.String(50), nullable=False),
        sa.Column("value", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index("idx_intel_sentiment_rollup_ws_bucket_name", "intel_daily_sentiment_rollups", ["workspace_id", "time_bucket", "sentiment"], unique=True)

    # 11. IntelDailyResolutionRollup
    op.create_table(
        "intel_daily_resolution_rollups",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("time_bucket", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolution_type", sa.String(50), nullable=False),
        sa.Column("value", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index("idx_intel_resolution_rollup_ws_bucket_name", "intel_daily_resolution_rollups", ["workspace_id", "time_bucket", "resolution_type"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("intel_daily_resolution_rollups")
    op.drop_table("intel_daily_sentiment_rollups")
    op.drop_table("intel_daily_intent_rollups")
    op.drop_table("intel_daily_topic_rollups")
    op.drop_table("conversation_summaries")
    op.drop_table("conversation_resolutions")
    op.drop_table("conversation_sentiments")
    op.drop_table("conversation_topics")
    op.drop_table("conversation_intents")
    op.drop_table("conversation_intelligence")
    op.drop_table("topic_registry")
