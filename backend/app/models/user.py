"""User model — platform users belonging to a workspace."""

import uuid

from sqlalchemy import Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="RESTRICT"),
        nullable=False,
    )
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="member")
    avatar_url = Column(Text, nullable=True)
    password_hash = Column(Text, nullable=False)  # Local JWT auth
    status = Column(String(20), nullable=False, default="active")

    # Relationships
    workspace = relationship("Workspace", back_populates="users", lazy="selectin")

    __table_args__ = (
        Index("idx_users_workspace", "workspace_id"),
        Index("idx_users_email", "email"),
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.id})>"
