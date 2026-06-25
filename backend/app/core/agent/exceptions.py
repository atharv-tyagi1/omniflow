class AgentRuntimeError(Exception):
    """Base exception for all agent runtime errors."""
    pass

class ProviderError(AgentRuntimeError):
    """Raised when an LLM provider fails (timeout, 5xx, etc.)."""
    pass

class PolicyViolationError(AgentRuntimeError):
    """Raised when an action violates a workspace or agent policy."""
    pass

class ToolExecutionError(AgentRuntimeError):
    """Raised when a tool fails to execute successfully."""
    pass

class ContextAssemblyError(AgentRuntimeError):
    """Raised when the context builder fails to construct the prompt."""
    pass
