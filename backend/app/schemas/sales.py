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
