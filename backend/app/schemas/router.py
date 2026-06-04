from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID


class AgentIntent(str, Enum):
    SALES = "sales"
    SUPPORT = "support"
    CUSTOMER_CARE = "customer_care"
    UNKNOWN = "unknown"


class RouterDecision(str, Enum):
    STAY = "stay"
    HANDOFF = "handoff"
    CLARIFY = "clarify"
    UNKNOWN = "unknown"


class IntentResult(BaseModel):
    """
    Structured output schema strictly enforced by the AIService/Gemini.
    """
    primary_intent: AgentIntent = Field(description="The primary identified intent category.")
    secondary_intent: Optional[AgentIntent] = Field(
        default=None, description="The secondary intent, if multiple intents exist."
    )
    confidence: float = Field(
        description="A confidence score between 0.0 and 1.0 representing how certain the model is."
    )


class RouteMessageRequest(BaseModel):
    conversation_id: UUID
    message: str = Field(description="The raw message from the user")


class RouteMessageResponse(BaseModel):
    decision: RouterDecision
    primary_intent: AgentIntent
    secondary_intent: Optional[AgentIntent] = None
    confidence: float
    active_agent: Optional[AgentIntent] = None
    previous_agent: Optional[AgentIntent] = None
    routed_agent: Optional[AgentIntent] = None
    handoff_required: bool
    route_reason: str
