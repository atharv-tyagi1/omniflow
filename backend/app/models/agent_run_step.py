"""AgentRunStep model — tracking individual steps within a run."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class AgentRunStep(Base):
    __tablename__ = "agent_run_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_type = Column(String(50), nullable=False)  # llm_call, tool_execution, rag_retrieval
    payload = Column(JSONB, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    workspace = relationship("Workspace", lazy="selectin")
    run = relationship("AgentRun", backref="steps", lazy="selectin")

    __table_args__ = (
        Index("idx_agent_run_steps_workspace", "workspace_id"),
        Index("idx_agent_run_steps_run", "run_id"),
    )

    def __repr__(self) -> str:
        return f"<AgentRunStep {self.step_type} for Run {self.run_id}>"
