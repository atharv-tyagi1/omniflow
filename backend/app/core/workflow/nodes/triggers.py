"""Trigger nodes implementation."""

from typing import Any, Dict
from backend.app.core.workflow.nodes.base import BaseNodeExecutor, NodeExecutionResult


class TriggerNode(BaseNodeExecutor):
    async def execute(self, context: Dict[str, Any]) -> NodeExecutionResult:
        # Triggers simply pass their initial payload (which is injected into context)
        # down to the next node.
        trigger_data = context.get("trigger_data", {})
        return NodeExecutionResult.success(output=trigger_data)
