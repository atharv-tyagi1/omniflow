"""Handoff model — records agent-to-agent handoffs during a conversation."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text, Float, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class Handoff(Base):
    __tablename__ = "handoffs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_agent = Column(String(50), nullable=False)
    to_agent = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    
    # Phase 11 tracking & idempotency
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=True,
    )
    confidence = Column(Float, nullable=True)
    trigger_intent = Column(String(50), nullable=True)
    previous_state = Column(JSONB, nullable=True)
    next_state = Column(JSONB, nullable=True)
    status = Column(String(20), nullable=False, default="completed")
    source_message_id = Column(String(255), nullable=True)
    
    # Lineage fields
    source_entity_type = Column(String(50), nullable=True)
    source_entity_id = Column(String(255), nullable=True)
    target_entity_type = Column(String(50), nullable=True)
    target_entity_id = Column(String(255), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    conversation = relationship(
        "Conversation", back_populates="handoffs", lazy="selectin"
    )

    workspace = relationship("Workspace", lazy="selectin")

    __table_args__ = (
        Index("idx_handoffs_conversation", "conversation_id"),
        UniqueConstraint("workspace_id", "conversation_id", "source_message_id", name="uq_handoff_source_message"),
    )

    def __repr__(self) -> str:
        return f"<Handoff {self.from_agent} → {self.to_agent} ({self.id})>"
