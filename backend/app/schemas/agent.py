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


class IntentMetadata(BaseModel):
    primary_intent: Optional[str] = None
    secondary_intent: Optional[str] = None
    confidence: Optional[float] = None

    def __getitem__(self, item):
        return getattr(self, item, None)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __contains__(self, item):
        return hasattr(self, item)

    def get(self, item, default=None):
        return getattr(self, item, default)


class AgentMetadata(BaseModel):
    issue_type: Optional[str] = None
    resolution_status: Optional[str] = None
    troubleshooting_steps: Optional[list[str]] = None
    sources: Optional[list[str]] = None
    complaint_type: Optional[str] = None
    refund_requested: Optional[bool] = None
    resolution_timeline: Optional[str] = None
    lead_score: Optional[int] = None
    next_best_action: Optional[str] = None
    intent: Optional[IntentMetadata] = None

    def __getitem__(self, item):
        val = getattr(self, item, None)
        if isinstance(val, BaseModel):
            return val.model_dump()
        return val

    def __setitem__(self, key, value):
        if key == "intent" and isinstance(value, dict):
            value = IntentMetadata(**value)
        setattr(self, key, value)

    def __contains__(self, item):
        return hasattr(self, item)

    def get(self, item, default=None):
        val = getattr(self, item, default)
        if isinstance(val, BaseModel):
            return val.model_dump()
        return val

    def keys(self):
        return self.model_fields.keys()

    def values(self):
        return [getattr(self, k) for k in self.keys()]

    def items(self):
        return [(k, getattr(self, k)) for k in self.keys()]


class AgentResponse(BaseModel):
    """Standardized response schema for all agent executions."""
    content: str = Field(description="The actual response text to the user.")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0.")
    sources: Optional[list[str]] = Field(default=None, description="List of knowledge base source IDs or URLs used.")
    agent_name: str = Field(description="The name of the agent that generated this response.")
    metadata: Optional[AgentMetadata] = Field(default=None, description="Optional metadata dictionary.")
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
