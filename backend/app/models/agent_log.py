"""AgentLog model — operational telemetry."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class AgentLog(Base):
    __tablename__ = "agent_logs"

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
    run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    level = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    workspace = relationship("Workspace", lazy="selectin")
    agent = relationship("Agent", lazy="selectin")

    __table_args__ = (
        Index("idx_agent_logs_workspace", "workspace_id"),
        Index("idx_agent_logs_agent", "agent_id"),
        Index("idx_agent_logs_run", "run_id"),
    )

    def __repr__(self) -> str:
        return f"<AgentLog {self.level} - {self.id}>"
