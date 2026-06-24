from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Numeric, Index, text
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

    # Phase 11 additive tracking fields
    handoff_recommended = Column(Boolean, default=False)
    next_agent = Column(String(50), nullable=True)
    source_agent = Column(String(50), nullable=True)
    
    # Phase 11 additive lineage fields
    parent_case_id = Column(UUID(as_uuid=True), ForeignKey("customer_care_cases.id", ondelete="SET NULL"), nullable=True)
    handoff_reason = Column(Text, nullable=True)
    handoff_stage = Column(String(50), nullable=True)
    source_channel = Column(String(50), nullable=True)

    __table_args__ = (
        Index("idx_cc_cases_workspace", "workspace_id"),
        Index("idx_cc_cases_ws_conv_stage", "workspace_id", "conversation_id", "current_stage"),
        Index("idx_cc_cases_ws_interaction", "workspace_id", "last_interaction_at"),
        Index("idx_cc_cases_ws_complaint", "workspace_id", "complaint_type"),
        # Concurrency safety: only one active case per conversation/workspace
        Index(
            "idx_cc_cases_unique_active",
            "workspace_id", "conversation_id",
            unique=True,
            postgresql_where=text("current_stage NOT IN ('resolved', 'closed')")
        )
    )
