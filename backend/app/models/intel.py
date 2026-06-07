"""Phase 13: Conversation Intel Models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from backend.app.models.base import Base, TimestampMixin

# Use generic JSON fallback for SQLite tests
JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class TopicRegistry(Base, TimestampMixin):
    """Canonical Topic Registry for normalizing intent and topic subjects."""
    __tablename__ = "topic_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    canonical_topic = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    aliases = Column(JSON_TYPE, nullable=False, default=list)  # List of strings
    category = Column(String(255), nullable=True)

    __table_args__ = (
        Index("idx_topic_registry_canonical", "workspace_id", "canonical_topic", unique=True),
    )


class ConversationIntelligence(Base, TimestampMixin):
    """Canonical root intelligence entity for a single conversation."""
    __tablename__ = "conversation_intelligence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)

    primary_intent = Column(String(255), nullable=True)
    sentiment = Column(String(50), nullable=True)
    resolution = Column(String(50), nullable=True)
    
    needs_review = Column(Boolean, nullable=False, default=False)
    raw_confidence = Column(Numeric(5, 2), nullable=True)
    review_reason = Column(String(255), nullable=True)
    
    analysis_schema_version = Column(Integer, nullable=False, default=1)
    analyzer_version = Column(String(50), nullable=False, default="1.0")
    analyzed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    conversation = relationship("Conversation", backref="intelligence_record", lazy="selectin", uselist=False)

    __table_args__ = (
        Index("idx_conv_intel_ws_conv", "workspace_id", "conversation_id", unique=True),
        Index("idx_conv_intel_analyzed_at", "workspace_id", "analyzed_at"),
    )


class ConversationIntent(Base):
    """Specific intents extracted from the conversation."""
    __tablename__ = "conversation_intents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)

    primary_intent = Column(String(255), nullable=False)
    secondary_intents = Column(JSON_TYPE, nullable=False, default=list)
    confidence = Column(Numeric(5, 2), nullable=True)
    
    analysis_schema_version = Column(Integer, nullable=False, default=1)
    analyzer_version = Column(String(50), nullable=False, default="1.0")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_conv_intent_ws_conv", "workspace_id", "conversation_id", unique=True),
    )


class ConversationTopic(Base):
    """Individual themes/subjects extracted from the conversation."""
    __tablename__ = "conversation_topics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)

    topic_name = Column(String(255), nullable=False)
    confidence = Column(Numeric(5, 2), nullable=True)
    needs_review = Column(Boolean, nullable=False, default=False)
    
    analysis_schema_version = Column(Integer, nullable=False, default=1)
    analyzer_version = Column(String(50), nullable=False, default="1.0")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_conv_topics_ws_conv", "workspace_id", "conversation_id"),
        Index("idx_conv_topics_name", "workspace_id", "topic_name"),
    )


class ConversationSentiment(Base):
    """Extracted emotion state of the conversation."""
    __tablename__ = "conversation_sentiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)

    sentiment = Column(String(50), nullable=False)
    confidence = Column(Numeric(5, 2), nullable=True)
    needs_review = Column(Boolean, nullable=False, default=False)

    analysis_schema_version = Column(Integer, nullable=False, default=1)
    analyzer_version = Column(String(50), nullable=False, default="1.0")
    analyzed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_conv_sentiment_ws_conv", "workspace_id", "conversation_id", unique=True),
    )


class ConversationResolution(Base):
    """Resolution outcome outcome mapping."""
    __tablename__ = "conversation_resolutions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)

    resolution_type = Column(String(50), nullable=False)
    confidence = Column(Numeric(5, 2), nullable=True)
    needs_review = Column(Boolean, nullable=False, default=False)

    analysis_schema_version = Column(Integer, nullable=False, default=1)
    analyzer_version = Column(String(50), nullable=False, default="1.0")
    analyzed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_conv_resolution_ws_conv", "workspace_id", "conversation_id", unique=True),
    )


class ConversationSummary(Base):
    """Extracted text summaries."""
    __tablename__ = "conversation_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)

    short_summary = Column(Text, nullable=False)
    long_summary = Column(Text, nullable=True)
    
    summary_version = Column(Integer, nullable=False, default=1)
    analysis_schema_version = Column(Integer, nullable=False, default=1)
    analyzer_version = Column(String(50), nullable=False, default="1.0")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_conv_summary_ws_conv", "workspace_id", "conversation_id", unique=True),
    )
