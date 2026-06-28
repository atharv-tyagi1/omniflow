"""Runtime Context — typed dataclass representing the fully assembled agent execution context."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass
class ToolPolicy:
    """Resolved tool policy for a single tool."""
    tool_type: str
    tool_config: Dict[str, Any] = field(default_factory=dict)
    allowed_inputs: Optional[Dict[str, Any]] = None
    allowed_outputs: Optional[Dict[str, Any]] = None
    rate_limit: Optional[int] = None
    approval_required: bool = False


@dataclass
class ModelConfig:
    """Resolved model configuration."""
    provider: str
    model_name: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeContext:
    """
    Fully assembled execution context for a single agent turn.
    Built deterministically in the approved order:
      Workspace Policies → System Prompt → Agent Prompt → Conversation Context
      → Workspace Memory → Agent Memory → Conversation Memory
      → Knowledge Retrieval → Tool Availability → Workflow Availability
      → Model Configuration → LLM Request
    """
    # Identifiers
    request_id: str
    workspace_id: UUID
    agent_id: UUID
    version_id: UUID
    conversation_id: UUID
    run_id: Optional[UUID] = None

    # Agent metadata
    agent_name: str = ""
    agent_category: str = ""
    is_public_allowed: bool = False

    # Assembled context blocks (in injection order)
    workspace_policies: str = ""
    system_prompt: str = ""
    agent_prompt: str = ""
    workspace_memory: str = ""
    agent_memory: str = ""
    conversation_memory: str = ""
    knowledge_context: str = ""

    # Tool & workflow config
    tool_policies: List[ToolPolicy] = field(default_factory=list)
    available_tool_names: List[str] = field(default_factory=list)

    # Model config
    model_config: Optional[ModelConfig] = None

    # Trace bookkeeping (populated during execution)
    memory_references: List[str] = field(default_factory=list)
    knowledge_references: List[str] = field(default_factory=list)
    tool_calls_trace: List[Dict[str, Any]] = field(default_factory=list)
    workflow_calls_trace: List[Dict[str, Any]] = field(default_factory=list)
    prompt_version_id: Optional[UUID] = None

    def to_log_dict(self) -> Dict[str, Any]:
        """Returns a structured dict safe for logging (no raw content)."""
        return {
            "request_id": self.request_id,
            "workspace_id": str(self.workspace_id),
            "agent_id": str(self.agent_id),
            "version_id": str(self.version_id),
            "conversation_id": str(self.conversation_id),
            "run_id": str(self.run_id) if self.run_id else None,
            "agent_name": self.agent_name,
            "agent_category": self.agent_category,
            "provider": self.model_config.provider if self.model_config else "unknown",
            "model": self.model_config.model_name if self.model_config else "unknown",
            "tools_available": self.available_tool_names,
            "has_workspace_memory": bool(self.workspace_memory),
            "has_agent_memory": bool(self.agent_memory),
            "has_conversation_memory": bool(self.conversation_memory),
            "has_knowledge": bool(self.knowledge_context),
        }
