"""AgentMetric model — rolled up metrics."""

import uuid
from datetime import date

from sqlalchemy import Column, Date, Float, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class AgentMetric(Base):
    __tablename__ = "agent_metrics"

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
    metric_date = Column(Date, nullable=False, default=date.today)
    total_tokens = Column(Integer, nullable=False, default=0)
    total_cost = Column(Float, nullable=False, default=0.0)
    total_conversations = Column(Integer, nullable=False, default=0)

    # Relationships
    workspace = relationship("Workspace", lazy="selectin")
    agent = relationship("Agent", lazy="selectin")

    __table_args__ = (
        Index("idx_agent_metrics_workspace", "workspace_id"),
        Index("idx_agent_metrics_agent", "agent_id"),
    )

    def __repr__(self) -> str:
        return f"<AgentMetric {self.agent_id} on {self.metric_date}>"
