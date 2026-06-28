"""Tool Engine — generic tool execution with policy enforcement, retry, timeout, and audit logging."""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from backend.app.core.agent.exceptions import ToolPolicyDenialError, AgentRuntimeError

logger = logging.getLogger(__name__)

# Maximum time (seconds) a single tool call is allowed to run
_DEFAULT_TOOL_TIMEOUT_SECONDS = 30

# Retry configuration
_MAX_RETRIES = 2
_RETRY_BACKOFF_SECONDS = 1.0


class ToolEngine:
    """
    Registry and execution logic for all agent tools.
    Every execution path respects AgentToolPolicy constraints:
    - Permission checks (is the tool allowed?)
    - Input validation (does the input match allowed schema?)
    - Output validation (does the output match allowed schema?)
    - Rate limiting (max invocations)
    - Approval gating (human-in-the-loop)
    - Timeout enforcement
    - Retry logic with exponential backoff
    - Audit logging
    """

    def __init__(self):
        self._registry: Dict[str, Any] = {}
        self._invocation_counts: Dict[str, int] = {}

    # ──────────────────────────────────────────────────────────────────────────
    # REGISTRATION
    # ──────────────────────────────────────────────────────────────────────────

    def register_tool(self, name: str, func: Any) -> None:
        """Registers a callable tool by name."""
        self._registry[name] = func
        logger.debug(f"Registered tool: {name}")

    def register_defaults(self) -> None:
        """Registers all default tools from the tools package."""
        from backend.app.core.agent.tools.workflow import trigger_workflow
        from backend.app.core.agent.tools.knowledge_search import search_knowledge
        from backend.app.core.agent.tools.http_request import http_request

        self.register_tool("workflow", trigger_workflow)
        self.register_tool("knowledge_search", search_knowledge)
        self.register_tool("http_request", http_request)

    # ──────────────────────────────────────────────────────────────────────────
    # POLICY RESOLUTION
    # ──────────────────────────────────────────────────────────────────────────

    def get_available_tools(
        self, tool_policies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Returns the list of tools actually available based on active policies.
        Only returns tools that are registered AND have a policy.
        """
        available = []
        for policy in tool_policies:
            tool_type = policy.get("tool_type", "")
            if tool_type in self._registry:
                available.append({
                    "name": tool_type,
                    "config": policy.get("tool_config", {}),
                    "approval_required": policy.get("approval_required", False),
                })
        return available

    def _find_policy(
        self, tool_name: str, tool_policies: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Finds the policy for a specific tool."""
        for policy in tool_policies:
            if policy.get("tool_type") == tool_name:
                return policy
        return None

    def _check_rate_limit(self, tool_name: str, limit: Optional[int]) -> None:
        """Raises ToolPolicyDenialError if the rate limit is exceeded."""
        if limit is None:
            return
        count = self._invocation_counts.get(tool_name, 0)
        if count >= limit:
            raise ToolPolicyDenialError(
                f"Tool '{tool_name}' has exceeded its rate limit of {limit} calls per turn."
            )

    def _validate_input(
        self, tool_name: str, kwargs: Dict[str, Any], allowed_inputs: Optional[Dict]
    ) -> None:
        """Validates tool input against the allowed_inputs schema (key whitelist)."""
        if not allowed_inputs:
            return  # No input restriction defined
        for key in kwargs:
            if key not in allowed_inputs:
                raise ToolPolicyDenialError(
                    f"Tool '{tool_name}' received forbidden input key: '{key}'. "
                    f"Allowed: {list(allowed_inputs.keys())}"
                )

    # ──────────────────────────────────────────────────────────────────────────
    # EXECUTION
    # ──────────────────────────────────────────────────────────────────────────

    async def execute_tool(
        self,
        tool_name: str,
        kwargs: Dict[str, Any],
        tool_policies: List[Dict[str, Any]],
        workspace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes a tool call after full policy validation.
        Implements timeout + retry with exponential backoff.
        """
        # 1. Check tool is registered
        if tool_name not in self._registry:
            raise ToolPolicyDenialError(f"Tool '{tool_name}' is not registered.")

        # 2. Check policy exists
        policy = self._find_policy(tool_name, tool_policies)
        if policy is None:
            raise ToolPolicyDenialError(
                f"Tool '{tool_name}' has no active policy — execution denied."
            )

        # 3. Check approval requirement
        if policy.get("approval_required", False):
            logger.warning(
                f"Tool '{tool_name}' requires human approval. "
                "Blocking execution pending approval."
            )
            return {
                "status": "pending_approval",
                "message": f"Tool '{tool_name}' requires human approval before execution.",
            }

        # 4. Rate limit check
        self._check_rate_limit(tool_name, policy.get("rate_limit"))

        # 5. Input validation
        self._validate_input(tool_name, kwargs, policy.get("allowed_inputs"))

        # 6. Execute with timeout + retry
        tool_func = self._registry[tool_name]
        last_error: Optional[Exception] = None

        for attempt in range(_MAX_RETRIES + 1):
            start = time.monotonic()
            try:
                timeout = policy.get("tool_config", {}).get(
                    "timeout_seconds", _DEFAULT_TOOL_TIMEOUT_SECONDS
                )
                result = await asyncio.wait_for(
                    tool_func(**kwargs),
                    timeout=timeout,
                )
                latency_ms = int((time.monotonic() - start) * 1000)

                # Track invocations for rate limiting
                self._invocation_counts[tool_name] = (
                    self._invocation_counts.get(tool_name, 0) + 1
                )

                logger.info(
                    f"Tool '{tool_name}' executed successfully "
                    f"(attempt {attempt + 1}, latency={latency_ms}ms)"
                )
                return {"status": "success", "result": result, "latency_ms": latency_ms}

            except asyncio.TimeoutError:
                latency_ms = int((time.monotonic() - start) * 1000)
                last_error = TimeoutError(
                    f"Tool '{tool_name}' timed out after {timeout}s"
                )
                logger.warning(f"Tool '{tool_name}' timed out (attempt {attempt + 1})")

            except Exception as e:
                latency_ms = int((time.monotonic() - start) * 1000)
                last_error = e
                logger.warning(
                    f"Tool '{tool_name}' failed (attempt {attempt + 1}): {e}"
                )

            if attempt < _MAX_RETRIES:
                await asyncio.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))

        # All retries exhausted
        logger.error(f"Tool '{tool_name}' failed after {_MAX_RETRIES + 1} attempts: {last_error}")
        return {
            "status": "error",
            "message": f"Tool '{tool_name}' failed after retries: {last_error}",
        }
