from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from decimal import Decimal
from enum import Enum
from uuid import UUID
from datetime import datetime

class CustomerCareStage(str, Enum):
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    REFUND_PENDING = "refund_pending"
    AWAITING_CUSTOMER = "awaiting_customer"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"

class ComplaintType(str, Enum):
    PRODUCT = "product"
    BILLING = "billing"
    SERVICE = "service"
    DELIVERY = "delivery"
    OTHER = "other"
    NONE = "none"

class CustomerSentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"

class CustomerCareAgentOutput(BaseModel):
    """
    Structured output requested from the LLM via Gemini for CustomerCareAgent.
    """
    customer_reply: str = Field(description="The response to display to the user, with high empathy.")
    complaint_type: ComplaintType = Field(description="The classified type of complaint.")
    order_id: Optional[str] = Field(default=None, description="Order ID if identified in the conversation.")
    account_issue_type: Optional[str] = Field(default=None, description="Account issue type if applicable.")
    refund_requested: bool = Field(default=False, description="Whether the user explicitly requested a refund.")
    refund_amount_requested: Optional[Decimal] = Field(default=None, description="Specific monetary amount requested for refund.")
    sentiment: CustomerSentiment = Field(description="Current detected sentiment of the user.")
    resolution_timeline: Optional[str] = Field(default=None, description="Clear timeline provided to the user, if resolution is not immediate.")
    resolution_status: CustomerCareStage = Field(description="The updated stage of the customer care case.")
    
    confidence: float = Field(description="Confidence score between 0.0 and 1.0.")
    sources: Optional[List[str]] = Field(default=None, description="RAG source references if used.")
    agent_name: str = Field(description="Name of the agent handling the request.")
    metadata: Optional[dict] = Field(default=None, description="Any additional tracking metadata.")
    
    requires_human: bool = Field(default=False, description="True if manual intervention, legal/chargeback handling, or unapproved compensation is needed.")
    handoff_recommended: bool = Field(default=False, description="True if the agent should hand off to another agent or human.")
    next_agent: Optional[str] = Field(default=None, description="Recommended next agent if handoff is true.")

class CustomerCareCaseResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    customer_id: UUID
    conversation_id: UUID
    complaint_type: Optional[ComplaintType]
    refund_requested: bool
    refund_amount_requested: Optional[Decimal]
    order_id: Optional[str]
    account_issue_type: Optional[str]
    sentiment: Optional[CustomerSentiment]
    current_stage: CustomerCareStage
    escalation_reason: Optional[str]
    resolution_timeline: Optional[str]
    last_interaction_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
