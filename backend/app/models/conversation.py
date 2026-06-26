"""Conversation model — chat sessions managed by the Agent Platform."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
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
    channel_id = Column(
        UUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="SET NULL"),
        nullable=True,
    )
    status = Column(String(50), nullable=False, default="active")
    active_participant_id = Column(UUID(as_uuid=True), nullable=True)
    last_responding_participant_id = Column(UUID(as_uuid=True), nullable=True)
    handoff_status = Column(String(50), nullable=False, default="none")  # pending, complete, none
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    workspace = relationship("Workspace", lazy="selectin")
    channel = relationship("Channel", lazy="selectin")
    participants = relationship("ConversationParticipant", backref="conversation", lazy="selectin")
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan", lazy="selectin"
    )
    handoffs = relationship(
        "Handoff", back_populates="conversation", cascade="all, delete-orphan", lazy="selectin"
    )
    topics = relationship(
        "Topic", back_populates="conversation", cascade="all, delete-orphan", lazy="selectin"
    )
    sentiments = relationship(
        "Sentiment", back_populates="conversation", cascade="all, delete-orphan", lazy="selectin"
    )
    voice_interactions = relationship(
        "VoiceInteraction", back_populates="conversation", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("idx_conversations_workspace", "workspace_id"),
        Index("idx_conversations_channel_id", "channel_id"),
    )

    def __repr__(self) -> str:
        return f"<Conversation {self.id}>"
