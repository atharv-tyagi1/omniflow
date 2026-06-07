"""Conversation model — chat sessions between customers and agents."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    current_agent = Column(String(50), nullable=True)
    previous_agent = Column(String(50), nullable=True)
    external_id = Column(String(255), nullable=True)  # New for Public API Integration
    handoff_count = Column(Integer, default=0, nullable=False)
    last_handoff_at = Column(DateTime(timezone=True), nullable=True)
    last_handoff_reason = Column(Text, nullable=True)
    current_state_version = Column(Integer, default=1, nullable=False)
    current_state = Column(JSONB, nullable=True)
    unresolved_intent = Column(String(50), nullable=True)
    loop_cooldown_until = Column(DateTime(timezone=True), nullable=True)
    channel = Column(
        String(50), nullable=False, default="web"
    )  # web | telegram_chat | telegram_voice
    status = Column(String(20), nullable=False, default="active")
    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    workspace = relationship("Workspace", lazy="selectin")
    customer = relationship("Customer", back_populates="conversations", lazy="selectin")
    messages = relationship("Message", back_populates="conversation", lazy="selectin")
    handoffs = relationship("Handoff", back_populates="conversation", lazy="selectin")
    sentiments = relationship(
        "Sentiment", back_populates="conversation", lazy="selectin"
    )
    topics = relationship("Topic", back_populates="conversation", lazy="selectin")
    voice_interactions = relationship(
        "VoiceInteraction", back_populates="conversation", lazy="selectin"
    )

    __table_args__ = (
        Index("idx_conversations_workspace", "workspace_id"),
        Index("idx_conversations_customer", "customer_id"),
        Index("idx_conversations_channel", "channel"),
        Index("idx_conversations_external", "external_id"),
        # Phase 13.5: Ensure unique external identities per workspace
        __import__("sqlalchemy").UniqueConstraint("workspace_id", "external_id", name="uq_workspace_conversation_external_id"),
    )

    def __repr__(self) -> str:
        return f"<Conversation {self.id} ({self.channel})>"
