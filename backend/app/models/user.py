"""User model — platform users belonging to a workspace."""

import uuid

from sqlalchemy import Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    avatar_url = Column(Text, nullable=True)
    password_hash = Column(Text, nullable=False)  # Local JWT auth
    status = Column(String(20), nullable=False, default="active")

    # Relationships
    workspaces = relationship("WorkspaceMember", back_populates="user", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        Index("idx_users_email", "email"),
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.id})>"
