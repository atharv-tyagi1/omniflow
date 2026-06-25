"""ConversationParticipant model — explicit active responder mapping."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from backend.app.models.base import Base


class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    participant_id = Column(UUID(as_uuid=True), primary_key=True)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    participant_type = Column(String(50), nullable=False)  # human, agent
    joined_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_conversation_participants_workspace", "workspace_id"),
    )

    def __repr__(self) -> str:
        return f"<ConversationParticipant {self.participant_type} {self.participant_id} in {self.conversation_id}>"
