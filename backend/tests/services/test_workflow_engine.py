import pytest
import uuid
import asyncio
from unittest.mock import patch, MagicMock

from backend.app.core.workflow.nodes.conditions import IfElseCondition
from backend.app.core.workflow.nodes.actions import WebhookAction
from backend.app.core.workflow.engine import WorkflowEngine, ExecutionContext

@pytest.mark.asyncio
async def test_condition_evaluator_true():
    config = {
        "variable": "trigger_data.payload.amount",
        "operator": "greater_than",
        "value": "100"
    }
    node = IfElseCondition("node_1", config)
    
    context = {"trigger_data": {"payload": {"amount": 150}}}
    result = await node.execute(context)
    
    assert result.status == "success"
    assert result.output.get("matched") is True

@pytest.mark.asyncio
async def test_condition_evaluator_false():
    config = {
        "variable": "trigger_data.payload.amount",
        "operator": "greater_than",
        "value": "100"
    }
    node = IfElseCondition("node_1", config)
    
    context = {"trigger_data": {"payload": {"amount": 50}}}
    result = await node.execute(context)
    
    assert result.status == "success"
    assert result.output.get("matched") is False

@pytest.mark.asyncio
async def test_ssrf_protection():
    config = {"url": "http://169.254.169.254/latest/meta-data/"}
    node = WebhookAction("node_1", config)
    
    result = await node.execute({})
    assert result.status == "failed"
    assert "SSRF" in result.error.get("error", "")

    config_local = {"url": "http://127.0.0.1/admin"}
    node_local = WebhookAction("node_2", config_local)
    
    result_local = await node_local.execute({})
    assert result_local.status == "failed"
    assert "SSRF" in result_local.error.get("error", "")

@pytest.mark.asyncio
async def test_engine_execution_flow():
    # Simple test for WorkflowEngine execution
    mock_session = MagicMock()
    engine = WorkflowEngine(mock_session)
    
    # Just asserting instantiation for now, as testing full DAG requires DB setup
    assert engine.node_timeout == 30.0
    assert engine.workflow_timeout == 300.0
