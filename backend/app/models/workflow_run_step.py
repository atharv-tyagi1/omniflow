"""WorkflowRunStep model — stores exact inputs/outputs for node execution."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class WorkflowRunStep(Base):
    __tablename__ = "workflow_run_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    node_id = Column(
        UUID(as_uuid=True),
        nullable=False,
    )
    status = Column(String(20), nullable=False)
    input_payload = Column(JSONB, nullable=True)
    output_payload = Column(JSONB, nullable=True)
    error_payload = Column(JSONB, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    run = relationship("WorkflowRun", back_populates="steps", lazy="selectin")

    __table_args__ = (
        Index("idx_workflow_run_steps_run", "run_id"),
        Index("idx_workflow_run_steps_node", "node_id"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowRunStep {self.node_id} ({self.status})>"
