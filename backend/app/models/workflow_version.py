"""WorkflowVersion model — snapshots of DAG configuration."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class WorkflowVersion(Base):
    __tablename__ = "workflow_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number = Column(Integer, nullable=False, default=1)
    is_published = Column(Boolean, nullable=False, default=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    workflow = relationship("Workflow", back_populates="versions", lazy="selectin")
    nodes = relationship("WorkflowNode", back_populates="version", lazy="selectin", cascade="all, delete-orphan")
    edges = relationship("WorkflowEdge", back_populates="version", lazy="selectin", cascade="all, delete-orphan")
    runs = relationship("WorkflowRun", back_populates="version", lazy="selectin")

    __table_args__ = (
        Index("idx_workflow_versions_workflow", "workflow_id"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowVersion {self.id} (Workflow: {self.workflow_id}, V{self.version_number})>"
