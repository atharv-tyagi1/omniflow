"""WorkflowEventQueue model — stores events to be processed dually."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.app.models.base import Base


class WorkflowEventQueue(Base):
    __tablename__ = "workflow_event_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type = Column(String(255), nullable=False)
    payload = Column(JSONB, nullable=False, default=dict)
    status = Column(String(50), nullable=False, default="pending")
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_workflow_event_queue_workspace", "workspace_id"),
        Index("idx_workflow_event_queue_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowEventQueue {self.event_type} ({self.status})>"
