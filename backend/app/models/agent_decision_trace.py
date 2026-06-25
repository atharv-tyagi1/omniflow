"""AgentDecisionTrace model — dedicated schema for massive trace metadata."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class AgentDecisionTrace(Base):
    __tablename__ = "agent_decision_traces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_step_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_run_steps.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    prompt_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_prompts.id", ondelete="SET NULL"),
        nullable=True,
    )
    memory_references = Column(JSONB, nullable=True)
    knowledge_references = Column(JSONB, nullable=True)
    tool_calls = Column(JSONB, nullable=True)
    workflow_calls = Column(JSONB, nullable=True)
    model_used = Column(String(255), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    cost_tokens = Column(Integer, nullable=True)
    execution_metadata = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    workspace = relationship("Workspace", lazy="selectin")
    run_step = relationship("AgentRunStep", backref="decision_trace", lazy="selectin")
    prompt_version = relationship("AgentPrompt", lazy="selectin")

    __table_args__ = (
        Index("idx_agent_decision_traces_workspace", "workspace_id"),
    )

    def __repr__(self) -> str:
        return f"<AgentDecisionTrace for Step {self.run_step_id}>"
