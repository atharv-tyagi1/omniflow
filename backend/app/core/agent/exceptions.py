"""Runtime Exceptions for Agent Execution."""

class AgentRuntimeError(Exception):
    """Base exception for all agent runtime errors."""
    pass

class ProviderTimeoutError(AgentRuntimeError):
    """Raised when the LLM provider times out."""
    pass

class ToolPolicyDenialError(AgentRuntimeError):
    """Raised when an agent attempts to use a tool improperly or beyond its policy."""
    pass

class MaxRecursionError(AgentRuntimeError):
    """Raised when the agent exceeds maximum tool calls or workflow hops per turn."""
    pass

class MemoryRetrievalError(AgentRuntimeError):
    """Raised when the runtime fails to retrieve required memory context."""
    pass

class ContextLimitExceededError(AgentRuntimeError):
    """Raised when the constructed context exceeds the model's maximum context window."""
    pass
