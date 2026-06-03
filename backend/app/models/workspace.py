"""Workspace model — represents a company / organization tenant."""

import uuid

from sqlalchemy import Column, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base, TimestampMixin


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=True)
    plan = Column(String(50), nullable=False, default="free")
    status = Column(String(20), nullable=False, default="active")

    # Relationships
    users = relationship("User", back_populates="workspace", lazy="selectin")

    __table_args__ = (
        Index("idx_workspaces_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Workspace {self.name} ({self.id})>"
