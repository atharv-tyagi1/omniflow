from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from backend.app.schemas.agent import AgentMetadata


class SupportIssueType(str, Enum):
    login = "login"
    payment = "payment"
    setup = "setup"
    usage = "usage"
    bug = "bug"
    account = "account"
    unknown = "unknown"


class ResolutionStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class SupportAgentOutput(BaseModel):
    """Structured schema returned by the LLM for Support interactions."""
    customer_reply: str = Field(..., description="The message content to show the customer.")
    issue_type: SupportIssueType = Field(..., description="The classified type of support issue.")
    probable_cause: Optional[str] = Field(default=None, description="The diagnosed probable cause of the issue, if any.")
    troubleshooting_steps: list[str] = Field(default_factory=list, description="A list of specific troubleshooting steps the agent has provided or is currently exploring.")
    resolution_status: ResolutionStatus = Field(..., description="The current status of the support case.")
    confidence: float = Field(..., description="Confidence score from 0.0 to 1.0 regarding the accuracy of the proposed solution.")
    sources: list[str] = Field(default_factory=list, description="List of knowledge base documentation or RAG sources used to generate the reply.")
    agent_name: str = Field(..., description="The name of the agent generating the response.")
    metadata: AgentMetadata = Field(default_factory=AgentMetadata, description="Additional context or metadata.")
    handoff_recommended: bool = Field(default=False, description="Set to true if handoff to another agent is recommended.")
    next_agent: Optional[str] = Field(default=None, description="The name of the agent to hand off to if required.")
    requires_human: bool = Field(default=False, description="Set to true if escalation to a human operator is required (e.g. unknown bugs, backend intervention needed).")
