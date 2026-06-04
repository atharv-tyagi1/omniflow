"""WorkspaceMember model — many-to-many relationship between Users and Workspaces."""

import uuid
from sqlalchemy import Column, ForeignKey, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base, TimestampMixin

class WorkspaceMember(Base, TimestampMixin):
    __tablename__ = "workspace_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(String(50), nullable=False, default="member")  # owner, admin, manager, member

    # Relationships
    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="workspaces")

    __table_args__ = (
        Index("idx_wsmember_workspace", "workspace_id"),
        Index("idx_wsmember_user", "user_id"),
        Index("idx_wsmember_workspace_user", "workspace_id", "user_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<WorkspaceMember ws={self.workspace_id} user={self.user_id} role={self.role}>"
