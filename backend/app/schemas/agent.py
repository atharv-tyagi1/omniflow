from pydantic import BaseModel, Field
from typing import Optional, Any
from backend.app.schemas.router import AgentIntent

# Alias AgentIntent to AgentType to maintain a single source of truth for the system
AgentType = AgentIntent


class AgentConfig(BaseModel):
    """Configuration overrides for a specific agent execution."""
    temperature: float = Field(default=0.7)
    top_p: float = Field(default=0.9)
    max_tokens: int = Field(default=1024)
    enable_rag: bool = Field(default=True)
    enable_history: bool = Field(default=True)


class AgentContext(BaseModel):
    """Structured context object passed into the prompt builder."""
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)
    rag_context: list[str] = Field(default_factory=list)
    workspace_context: dict[str, Any] = Field(default_factory=dict)
    customer_context: dict[str, Any] = Field(default_factory=dict)
    conversation_state: dict[str, Any] = Field(default_factory=dict)
    router_metadata: dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Standardized response schema for all agent executions."""
    content: str = Field(description="The actual response text to the user.")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0.")
    sources: Optional[list[str]] = Field(default=None, description="List of knowledge base source IDs or URLs used.")
    agent_name: str = Field(description="The name of the agent that generated this response.")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="Optional metadata dictionary.")
    handoff_recommended: bool = Field(default=False, description="True if the agent believes another agent should take over.")
    next_agent: Optional[str] = Field(default=None, description="The suggested agent to hand off to, if applicable.")
    sentiment: str = Field(default="neutral", description="Detected sentiment of the user interaction.")
    requires_human: bool = Field(default=False, description="True if a human agent must intervene.")


class AgentMetrics(BaseModel):
    """Observability tracking metrics for each agent execution."""
    agent_name: str
    latency_ms: int
    token_usage: int
    confidence: float
    handoff_recommended: bool
