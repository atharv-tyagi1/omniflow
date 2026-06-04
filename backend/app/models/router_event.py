"""RouterEvent model — records intelligent routing decisions for analytics."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class RouterEvent(Base):
    __tablename__ = "router_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    primary_intent = Column(String(50), nullable=False)
    secondary_intent = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=False)
    decision = Column(String(50), nullable=False)
    routed_agent = Column(String(50), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    conversation = relationship(
        "Conversation", backref="router_events", lazy="selectin"
    )

    __table_args__ = (Index("idx_router_events_conversation", "conversation_id"),)

    def __repr__(self) -> str:
        return f"<RouterEvent {self.decision} ({self.id})>"
