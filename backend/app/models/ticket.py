"""Ticket model — support tickets created from conversations."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(20), nullable=False, default="medium")  # low | medium | high | critical
    status = Column(String(20), nullable=False, default="open")  # open | in_progress | resolved | closed
    assigned_to = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    workspace = relationship("Workspace", lazy="selectin")
    customer = relationship("Customer", back_populates="tickets", lazy="selectin")
    conversation = relationship("Conversation", lazy="selectin")
    assignee = relationship("User", lazy="selectin")

    __table_args__ = (
        Index("idx_tickets_workspace", "workspace_id"),
        Index("idx_tickets_status", "status"),
        Index("idx_tickets_priority", "priority"),
    )

    def __repr__(self) -> str:
        return f"<Ticket {self.title} ({self.id})>"
