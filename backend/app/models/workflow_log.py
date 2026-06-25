"""WorkflowLog model — stores audit events for workflows."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class WorkflowLog(Base):
    __tablename__ = "workflow_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    workflow_id = Column(UUID(as_uuid=True), nullable=True)
    run_id = Column(UUID(as_uuid=True), nullable=True)
    step_id = Column(UUID(as_uuid=True), nullable=True)
    event_type = Column(String(100), nullable=False)
    message = Column(String(1000), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_workflow_logs_workspace", "workspace_id"),
        Index("idx_workflow_logs_workflow", "workflow_id"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowLog {self.event_type} - {self.message}>"
