from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class SalesFunnelStage(str, Enum):
    new = "new"
    discovery = "discovery"
    qualified = "qualified"
    objection = "objection"
    ready_to_buy = "ready_to_buy"
    converted = "converted"
    lost = "lost"


class BuyingIntent(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class LeadQualification(BaseModel):
    """Structured extraction schema used by the SalesAgent to qualify leads."""
    budget: Optional[str] = Field(default=None, description="The customer's declared budget range.")
    urgency: Optional[str] = Field(default=None, description="The customer's timeframe for purchasing.")
    company_size: Optional[str] = Field(default=None, description="Size of the customer's company.")
    use_case: Optional[str] = Field(default=None, description="The primary problem the customer is trying to solve.")
    buying_intent: Optional[BuyingIntent] = Field(default=None, description="The inferred intent level to purchase.")

class SalesAgentOutput(BaseModel):
    """Structured schema returned by the LLM for Sales interactions."""
    customer_reply: str = Field(..., description="The message content to show the customer.")
    lead_score: Optional[int] = Field(default=None, description="The inferred lead score from 1-100.")
    budget: Optional[str] = Field(default=None, description="The customer's declared budget range.")
    urgency: Optional[str] = Field(default=None, description="The customer's timeframe for purchasing.")
    company_size: Optional[str] = Field(default=None, description="Size of the customer's company.")
    use_case: Optional[str] = Field(default=None, description="The primary problem the customer is trying to solve.")
    buying_intent: Optional[BuyingIntent] = Field(default=None, description="The inferred intent level to purchase.")
    current_stage: Optional[SalesFunnelStage] = Field(default=None, description="The sales stage this lead is in.")
    objections: list[str] = Field(default_factory=list, description="List of any objections the user has raised.")
    requires_human: bool = Field(default=False, description="Set to true if escalation triggers are hit.")
    handoff_recommended: bool = Field(default=False, description="Set to true if handoff to another agent is recommended.")
    next_agent: Optional[str] = Field(default=None, description="The name of the agent to hand off to if required.")
    next_best_action: Optional[str] = Field(default=None, description="Recommended next action for sales.")
