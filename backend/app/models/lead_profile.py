"""LeadProfile model — tracks prospective sales leads and funnel progression."""

import uuid
from datetime import datetime

from sqlalchemy import Column, ForeignKey, String, Enum as SQLEnum, Integer, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from backend.app.models.base import Base, TimestampMixin
from backend.app.schemas.sales import SalesFunnelStage, BuyingIntent


class LeadProfile(Base, TimestampMixin):
    __tablename__ = "lead_profiles"

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
    
    # Qualification data
    company_size = Column(String(100), nullable=True)
    budget = Column(String(100), nullable=True)
    urgency = Column(String(100), nullable=True)
    use_case = Column(String(500), nullable=True)
    
    # Funnel metadata
    buying_intent = Column(SQLEnum(BuyingIntent), nullable=True)
    current_stage = Column(SQLEnum(SalesFunnelStage), nullable=False, default=SalesFunnelStage.new)
    objections = Column(JSONB, nullable=True, default=list)
    lead_score = Column(Integer, nullable=True)
    
    # Interaction tracking
    last_interaction_at = Column(DateTime(timezone=True), nullable=True)
    last_stage_change_at = Column(DateTime(timezone=True), nullable=True)
    source_channel = Column(String(100), nullable=True)
    next_best_action = Column(String(500), nullable=True)

    # Relationships
    workspace = relationship("Workspace", lazy="selectin")
    customer = relationship("Customer", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("workspace_id", "customer_id", name="uq_lead_workspace_customer"),
        Index("idx_leads_workspace_stage", "workspace_id", "current_stage"),
        Index("idx_leads_workspace_intent", "workspace_id", "buying_intent"),
        Index("idx_leads_workspace_interaction", "workspace_id", "last_interaction_at"),
    )

    def __repr__(self) -> str:
        return f"<LeadProfile {self.id} (Stage: {self.current_stage})>"
