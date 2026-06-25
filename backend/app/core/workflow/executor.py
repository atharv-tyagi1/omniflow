"""Node Execution Factory and Dispatcher."""

from typing import Any, Dict
from backend.app.core.workflow.nodes.base import BaseNodeExecutor
from backend.app.core.workflow.nodes.triggers import TriggerNode
from backend.app.core.workflow.nodes.conditions import IfElseCondition
from backend.app.core.workflow.nodes.actions import WebhookAction, AddTagAction

class NodeExecutorFactory:
    @staticmethod
    def get_executor(node_id: str, node_type: str, config: Dict[str, Any]) -> BaseNodeExecutor:
        # Triggers
        if node_type.startswith("trigger."):
            return TriggerNode(node_id, config)
            
        # Conditions
        elif node_type == "condition.if_else":
            return IfElseCondition(node_id, config)
            
        # Actions
        elif node_type == "action.webhook_action":
            return WebhookAction(node_id, config)
        elif node_type == "action.add_tag":
            return AddTagAction(node_id, config)
            
        raise ValueError(f"Unknown node type: {node_type}")
