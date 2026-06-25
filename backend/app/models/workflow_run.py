"""WorkflowRun model — execution records for workflows."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_versions.id", ondelete="CASCADE"),
        nullable=True,
    )
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending | running | success | failed
    execution_log = Column(JSONB, nullable=True)
    executed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    workflow = relationship("Workflow", back_populates="runs", lazy="selectin")
    version = relationship("WorkflowVersion", back_populates="runs", lazy="selectin")
    steps = relationship("WorkflowRunStep", back_populates="run", lazy="selectin", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_workflow_runs_workflow", "workflow_id"),
        Index("idx_workflow_runs_version", "version_id"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowRun {self.id} ({self.status})>"
