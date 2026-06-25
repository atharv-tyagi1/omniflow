"""ConversationMemory model — active conversational turn storage."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class ConversationMemory(Base):
    __tablename__ = "conversation_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(String(50), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    workspace = relationship("Workspace", lazy="selectin")
    conversation = relationship("Conversation", lazy="selectin")

    __table_args__ = (
        Index("idx_conversation_memory_workspace", "workspace_id"),
        Index("idx_conversation_memory_conversation", "conversation_id"),
    )

    def __repr__(self) -> str:
        return f"<ConversationMemory {self.id}>"
