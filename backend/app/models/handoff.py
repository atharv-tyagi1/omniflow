"""Handoff model — records agent-to-agent handoffs during a conversation."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
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
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="handoffs", lazy="selectin")

    __table_args__ = (
        Index("idx_handoffs_conversation", "conversation_id"),
    )

    def __repr__(self) -> str:
        return f"<Handoff {self.from_agent} → {self.to_agent} ({self.id})>"
