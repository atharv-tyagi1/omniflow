"""Message model — individual messages within a conversation."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_type = Column(
        String(50), nullable=False
    )  # customer | sales_agent | support_agent | customer_care_agent | system
    content = Column(Text, nullable=False)
    message_type = Column(String(50), nullable=False, default="text")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    conversation = relationship(
        "Conversation", back_populates="messages", lazy="selectin"
    )

    __table_args__ = (
        Index("idx_messages_conversation", "conversation_id"),
        Index("idx_messages_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Message {self.id} ({self.sender_type})>"
