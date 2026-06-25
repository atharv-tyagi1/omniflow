"""AgentRun model — tracking individual agent execution lifecycles."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(String(50), nullable=False, default="running")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    workspace = relationship("Workspace", lazy="selectin")
    agent = relationship("Agent", lazy="selectin")
    version = relationship("AgentVersion", lazy="selectin")
    conversation = relationship("Conversation", lazy="selectin")

    __table_args__ = (
        Index("idx_agent_runs_workspace", "workspace_id"),
        Index("idx_agent_runs_conversation", "conversation_id"),
    )

    def __repr__(self) -> str:
        return f"<AgentRun {self.id} for Agent {self.agent_id}>"
