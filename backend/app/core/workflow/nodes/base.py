"""Base definitions for workflow nodes."""

from typing import Any, Dict
from abc import ABC, abstractmethod


class NodeExecutionResult:
    def __init__(self, status: str, output: Dict[str, Any] = None, error: Dict[str, Any] = None):
        self.status = status  # 'success', 'failed', 'running', 'skipped'
        self.output = output or {}
        self.error = error

    @classmethod
    def success(cls, output: Dict[str, Any] = None) -> "NodeExecutionResult":
        return cls(status="success", output=output)

    @classmethod
    def failed(cls, error: Dict[str, Any]) -> "NodeExecutionResult":
        return cls(status="failed", error=error)

    @classmethod
    def skipped(cls) -> "NodeExecutionResult":
        return cls(status="skipped")


class BaseNodeExecutor(ABC):
    def __init__(self, node_id: str, config: Dict[str, Any]):
        self.node_id = node_id
        self.config = config

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> NodeExecutionResult:
        """Execute the node logic using the current execution context."""
        pass
