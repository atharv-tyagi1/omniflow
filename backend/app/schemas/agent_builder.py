from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class AgentModelConfig(BaseModel):
    provider: str
    model_name: str
    config: Dict[str, Any]

class AgentPromptConfig(BaseModel):
    system_prompt: str
    welcome_prompt: Optional[str] = None
    fallback_prompt: Optional[str] = None

class AgentVersionResponse(BaseModel):
    id: uuid.UUID
    version_number: int
    is_published: bool
    created_at: datetime
    prompt: Optional[AgentPromptConfig] = None
    model: Optional[AgentModelConfig] = None
    
    class Config:
        from_attributes = True

class AgentListResponse(BaseModel):
    id: uuid.UUID
    name: str
    category: str
    is_active: bool
    created_at: datetime
    active_version_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True

class AgentDetailResponse(AgentListResponse):
    versions: List[AgentVersionResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True

class AgentCreateRequest(BaseModel):
    name: str
    category: str
    is_active: bool = True

class AgentVersionCreateRequest(BaseModel):
    prompt: AgentPromptConfig
    model: AgentModelConfig
    publish: bool = True


# ─────────────────────────────────────────────────────────────────────────────
# Phase 21.2E — Runtime API Schemas
# ─────────────────────────────────────────────────────────────────────────────

class AgentChatRequest(BaseModel):
    """Payload for POST /agents/{agent_id}/chat"""
    message: str
    conversation_id: Optional[uuid.UUID] = None  # Auto-created if omitted
    workspace_policies: Optional[str] = None


class AgentChatResponse(BaseModel):
    """Response from a single chat turn."""
    request_id: str
    content: str
    status: str
    run_id: Optional[uuid.UUID] = None
    conversation_id: uuid.UUID
    latency_ms: int
    tokens_used: int
    knowledge_used: bool
    memory_used: bool
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)


class AgentRunSummary(BaseModel):
    """Summary row for a single AgentRun."""
    id: uuid.UUID
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    conversation_id: uuid.UUID

    class Config:
        from_attributes = True


class AgentRunDetail(AgentRunSummary):
    """Detailed run view including steps and decision trace."""
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    decision_trace: Optional[Dict[str, Any]] = None


class ToolPolicyRequest(BaseModel):
    """Create or update a tool policy on an agent version."""
    tool_type: str
    tool_config: Dict[str, Any] = Field(default_factory=dict)
    allowed_inputs: Optional[Dict[str, Any]] = None
    allowed_outputs: Optional[Dict[str, Any]] = None
    rate_limit: Optional[int] = None
    approval_required: bool = False


class ToolPolicyResponse(ToolPolicyRequest):
    id: uuid.UUID
    version_id: uuid.UUID

    class Config:
        from_attributes = True


class AgentPublishRequest(BaseModel):
    """Publish a draft version."""
    version_id: uuid.UUID


class ToolPolicyListResponse(BaseModel):
    """Response list wrapper for tool policies."""
    policies: List[ToolPolicyResponse]


class AgentRunListResponse(BaseModel):
    runs: List[AgentRunSummary]


class AgentCloneRequest(BaseModel):
    """Payload for cloning an existing agent."""
    new_name: str
    category: Optional[str] = None


class SandboxExecuteRequest(BaseModel):
    """Payload for executing a draft version of an agent."""
    message: str
    conversation_id: Optional[uuid.UUID] = None
    force_draft: bool = True


class AgentDryRunResponse(BaseModel):
    """Response payload for a dry-run execution."""
    success: bool
    simulated_tools: List[str]
    latency_ms: int


class StreamEventResponse(BaseModel):
    """SSE streaming response envelope."""
    event: str
    data: Dict[str, Any]
    id: Optional[str] = None


class AgentTemplateResponse(BaseModel):
    """Response payload for listing agent templates."""
    id: uuid.UUID
    name: str
    description: str
    category: str
    is_global: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
