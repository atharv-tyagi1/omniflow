import pytest
import uuid
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.main import app
from backend.app.models.workflow_version import WorkflowVersion, WorkflowNode, WorkflowEdge
from backend.app.models.workflow_run import WorkflowRun
from backend.app.models.workflow_run_step import WorkflowRunStep
from backend.app.models.workflow_log import WorkflowLog
from backend.app.models.workflow_event_queue import WorkflowEventQueue
from backend.app.models.workflow import Workflow

@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

# VERIFICATION 1: E2E Execution & Correctness
@pytest.mark.asyncio
async def test_v1_e2e_workflow(async_client, mock_db_session: AsyncSession):
    # Setup mock user & workspace
    from backend.app.models.workspace import Workspace
    ws = Workspace(id=uuid.uuid4(), name="Test WS")
    mock_db_session.add(ws)
    await mock_db_session.commit()

    # 1. Create Workflow
    wf_payload = {"name": "E2E Verify", "description": "Verification 1"}
    # Note: Using mock_db_session for direct DB inserts to bypass auth complexity in tests if auth is not mocked
    wf = Workflow(id=uuid.uuid4(), workspace_id=ws.id, name="E2E Verify")
    mock_db_session.add(wf)
    await mock_db_session.commit()

    # Draft
    draft_data = {
        "nodes": [
            {"id": "n1", "type": "trigger.manual", "position": {"x": 0, "y": 0}, "config": {}},
            {"id": "n2", "type": "action.create_task", "position": {"x": 100, "y": 0}, "config": {"task_name": "Review"}},
            {"id": "n3", "type": "action.add_tag", "position": {"x": 200, "y": 0}, "config": {"tag": "Priority"}},
            {"id": "n4", "type": "action.webhook_action", "position": {"x": 300, "y": 0}, "config": {"url": "http://example.com/update_customer"}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n3", "target": "n4"},
        ]
    }
    
    from backend.app.services.workflow_builder_service import WorkflowBuilderService
    svc = WorkflowBuilderService(mock_db_session)
    from backend.app.schemas.workflow_builder import WorkflowDraftUpdate, WorkflowNodeSchema, WorkflowEdgeSchema
    await svc.update_draft(wf.id, WorkflowDraftUpdate(
        nodes=[WorkflowNodeSchema(**n) for n in draft_data["nodes"]],
        edges=[WorkflowEdgeSchema(**e) for e in draft_data["edges"]]
    ))

    # Publish
    version = await svc.publish_workflow(wf.id)
    assert version.is_published is True

    # Execute
    from backend.app.services.workflow_service import WorkflowService
    exec_svc = WorkflowService(mock_db_session)
    run_id = await exec_svc.dispatch_event(wf.id, {"trigger": "manual"})

    # Check Run
    run = await exec_svc.get_run_details(wf.id, run_id)
    assert run is not None
    assert run["status"] in ["queued", "running", "success"]

# VERIFICATION 3: Version Immutability
@pytest.mark.asyncio
async def test_v3_version_immutability(mock_db_session: AsyncSession):
    wf = Workflow(id=uuid.uuid4(), workspace_id=uuid.uuid4(), name="Immutability")
    mock_db_session.add(wf)
    await mock_db_session.commit()

    svc = WorkflowBuilderService(mock_db_session)
    # Draft V1
    await svc.update_draft(wf.id, WorkflowDraftUpdate(nodes=[], edges=[]))
    v1 = await svc.publish_workflow(wf.id)
    assert v1.version_number == 1

    # Draft V2
    await svc.update_draft(wf.id, WorkflowDraftUpdate(nodes=[WorkflowNodeSchema(id="n1", type="trigger.manual", position={"x":0,"y":0}, config={})], edges=[]))
    v2 = await svc.publish_workflow(wf.id)
    assert v2.version_number == 2
    assert v2.id != v1.id

    # Ensure V1 is untouched
    stmt = select(WorkflowVersion).where(WorkflowVersion.id == v1.id)
    v1_db = (await mock_db_session.execute(stmt)).scalar_one()
    assert len(v1_db.nodes) == 0

# VERIFICATION 7: Webhook Security
@pytest.mark.asyncio
async def test_v7_webhook_security(async_client):
    wf_id = str(uuid.uuid4())
    # No signature
    response = await async_client.post(f"/api/v1/workflows/webhooks/{wf_id}", json={"payload": 1})
    assert response.status_code == 401

    # Invalid signature
    response = await async_client.post(f"/api/v1/workflows/webhooks/{wf_id}", json={"payload": 1}, headers={"X-OmniFlow-Signature": "invalid"})
    assert response.status_code == 401

