"""Condition nodes implementation."""

from typing import Any, Dict
from backend.app.core.workflow.nodes.base import BaseNodeExecutor, NodeExecutionResult


class IfElseCondition(BaseNodeExecutor):
    async def execute(self, context: Dict[str, Any]) -> NodeExecutionResult:
        variable = self.config.get("variable")
        operator = self.config.get("operator")
        value = self.config.get("value")

        if not variable or not operator:
            return NodeExecutionResult.failed({"error": "Missing variable or operator config"})

        # Resolve variable from context
        # Format: trigger_data.customer.id -> context["trigger_data"]["customer"]["id"]
        actual_val = self._resolve_variable(variable, context)

        matched = False
        if operator == "equals":
            matched = str(actual_val) == str(value)
        elif operator == "contains":
            matched = str(value) in str(actual_val)
        elif operator == "not_equals":
            matched = str(actual_val) != str(value)
        elif operator == "greater_than":
            try:
                matched = float(actual_val) > float(value)
            except (ValueError, TypeError):
                matched = False
        
        return NodeExecutionResult.success(output={"matched": matched})

    def _resolve_variable(self, path: str, context: Dict[str, Any]) -> Any:
        parts = path.split(".")
        current = context
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current
