from typing import Any, Dict, Optional, Callable
import asyncio

from backend.app.core.agent.exceptions import ToolExecutionError, PolicyViolationError
from backend.app.models.agent_tool_policy import AgentToolPolicy

class ToolEngine:
    """
    Registry and execution logic for tools.
    Validates against AgentToolPolicy, handling timeouts, retries, and validations.
    """
    _registry: Dict[str, Callable] = {}

    @classmethod
    def register_tool(cls, name: str, func: Callable):
        cls._registry[name] = func

    @classmethod
    def get_tool(cls, name: str) -> Optional[Callable]:
        return cls._registry.get(name)

    @staticmethod
    async def execute_tool(
        tool_name: str,
        kwargs: Dict[str, Any],
        policy: Optional[AgentToolPolicy] = None
    ) -> Any:
        """
        Executes a tool with policy enforcement (timeout, retry budget, permissions).
        """
        func = ToolEngine.get_tool(tool_name)
        if not func:
            raise ToolExecutionError(f"Tool '{tool_name}' not found.")

        # Policy checks
        if policy:
            if not policy.is_active:
                raise PolicyViolationError(f"Tool '{tool_name}' is disabled by policy.")
            if policy.requires_approval:
                # In a real environment, this would suspend for human-in-the-loop
                raise PolicyViolationError(f"Tool '{tool_name}' requires manual approval, which is not supported in this run.")

        timeout_sec = policy.timeout_seconds if policy else 30
        max_retries = policy.max_retries if policy else 1

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                # We use asyncio.wait_for to enforce tool timeout policy
                return await asyncio.wait_for(func(**kwargs), timeout=timeout_sec)
            except asyncio.TimeoutError:
                last_error = ToolExecutionError(f"Tool '{tool_name}' timed out after {timeout_sec}s.")
            except Exception as e:
                last_error = ToolExecutionError(f"Tool '{tool_name}' execution failed: {str(e)}")
            
            # Simple exponential backoff for retries
            if attempt < max_retries:
                await asyncio.sleep(1 * (2 ** attempt))

        raise last_error
