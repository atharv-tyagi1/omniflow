"""Customer model — end-customers belonging to a workspace."""

import uuid

from sqlalchemy import Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base, TimestampMixin


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    telegram_id = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default="active")

    # Relationships
    workspace = relationship("Workspace", lazy="selectin")
    conversations = relationship("Conversation", back_populates="customer", lazy="selectin")
    tickets = relationship("Ticket", back_populates="customer", lazy="selectin")

    __table_args__ = (
        Index("idx_customers_workspace", "workspace_id"),
        Index("idx_customers_email", "email"),
        Index("idx_customers_telegram", "telegram_id"),
    )

    def __repr__(self) -> str:
        return f"<Customer {self.name} ({self.id})>"
