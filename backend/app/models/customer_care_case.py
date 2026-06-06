from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

from backend.app.models.base import Base, TimestampMixin

class CustomerCareCase(Base, TimestampMixin):
    __tablename__ = "customer_care_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    
    complaint_type = Column(String(50), nullable=True) # Strict enum validation in schema/service
    refund_requested = Column(Boolean, default=False)
    refund_amount_requested = Column(Numeric(12, 2), nullable=True)
    order_id = Column(String(100), nullable=True)
    account_issue_type = Column(String(100), nullable=True)
    
    sentiment = Column(String(20), nullable=True) # Strict enum validation in schema/service
    current_stage = Column(String(50), nullable=False, default="acknowledged") # Strict enum validation
    
    escalation_reason = Column(Text, nullable=True)
    resolution_timeline = Column(String(255), nullable=True)
    
    last_interaction_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_cc_cases_workspace", "workspace_id"),
        Index("idx_cc_cases_ws_conv", "workspace_id", "conversation_id"),
        Index("idx_cc_cases_ws_stage", "workspace_id", "current_stage"),
    )
