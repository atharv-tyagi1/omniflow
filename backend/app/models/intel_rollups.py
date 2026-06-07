"""Phase 13: Conversation Intel Rollups."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from backend.app.models.base import Base, TimestampMixin


class IntelDailyTopicRollup(Base, TimestampMixin):
    """Daily materialized aggregation of topics for high-performance trend querying."""
    __tablename__ = "intel_daily_topic_rollups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    time_bucket = Column(DateTime(timezone=True), nullable=False)  # TRUNC to DAY

    topic_name = Column(String(255), nullable=False)
    value = Column(Numeric(12, 2), nullable=False, default=0)

    __table_args__ = (
        Index("idx_intel_topic_rollup_ws_bucket_name", "workspace_id", "time_bucket", "topic_name", unique=True),
    )


class IntelDailyIntentRollup(Base, TimestampMixin):
    """Daily materialized aggregation of intents."""
    __tablename__ = "intel_daily_intent_rollups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    time_bucket = Column(DateTime(timezone=True), nullable=False)

    intent_name = Column(String(255), nullable=False)
    value = Column(Numeric(12, 2), nullable=False, default=0)

    __table_args__ = (
        Index("idx_intel_intent_rollup_ws_bucket_name", "workspace_id", "time_bucket", "intent_name", unique=True),
    )


class IntelDailySentimentRollup(Base, TimestampMixin):
    """Daily materialized aggregation of sentiment."""
    __tablename__ = "intel_daily_sentiment_rollups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    time_bucket = Column(DateTime(timezone=True), nullable=False)

    sentiment = Column(String(50), nullable=False)
    value = Column(Numeric(12, 2), nullable=False, default=0)

    __table_args__ = (
        Index("idx_intel_sentiment_rollup_ws_bucket_name", "workspace_id", "time_bucket", "sentiment", unique=True),
    )


class IntelDailyResolutionRollup(Base, TimestampMixin):
    """Daily materialized aggregation of resolutions."""
    __tablename__ = "intel_daily_resolution_rollups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    time_bucket = Column(DateTime(timezone=True), nullable=False)

    resolution_type = Column(String(50), nullable=False)
    value = Column(Numeric(12, 2), nullable=False, default=0)

    __table_args__ = (
        Index("idx_intel_resolution_rollup_ws_bucket_name", "workspace_id", "time_bucket", "resolution_type", unique=True),
    )
