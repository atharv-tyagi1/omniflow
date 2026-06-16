from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class HandoffStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentType(str, Enum):
    SALES = "sales"
    SUPPORT = "support"
    CUSTOMER_CARE = "customer_care"
    HUMAN = "human"
    UNKNOWN = "unknown"

class HandoffReason(str, Enum):
    TECHNICAL_ISSUE = "technical_issue"
    REFUND_REQUEST = "refund_request"
    COMPLAINT = "complaint"
    SALES_INQUIRY = "sales_inquiry"
    LOOP_PREVENTION = "loop_prevention"
    EXCEED_DEPTH = "exceed_depth"
    UNKNOWN = "unknown"

class IntentType(str, Enum):
    TROUBLESHOOT = "troubleshoot"
    BUY_PRODUCT = "buy_product"
    REFUND = "refund"
    COMPLAIN = "complain"
    UNKNOWN = "unknown"

    @classmethod
    def from_agent_intent(cls, agent_intent: str) -> "IntentType":
        mapping = {
            "sales": cls.BUY_PRODUCT,
            "support": cls.TROUBLESHOOT,
            "customer_care": cls.COMPLAIN,
        }
        if agent_intent in mapping:
            return mapping[agent_intent]
        try:
            return cls(agent_intent)
        except ValueError:
            return cls.UNKNOWN


class ConversationHandoffStateV1(BaseModel):
    """
    Versioned state for bounded JSONB storage.
    Ensures we don't dump entire conversation history into the json blob.
    """
    active_agent: Optional[AgentType] = None
    previous_agent: Optional[AgentType] = None
    unresolved_intent: Optional[IntentType] = None
    handoff_summary: Optional[str] = None
    cooldown_active: bool = False
    cooldown_until: Optional[str] = None  # ISO format string for JSON serializability

class HandoffDecision(BaseModel):
    """
    Output from the HandoffRuleEngine indicating routing instruction.
    """
    should_handoff: bool
    to_agent: Optional[AgentType] = None
    reason: Optional[HandoffReason] = None
    confidence: float = 1.0
    context_summary: Optional[str] = None
