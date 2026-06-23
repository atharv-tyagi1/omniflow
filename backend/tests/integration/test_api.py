import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_openapi_route(async_client: AsyncClient):
    """Test that OpenAPI is accessible at the root."""
    response = await async_client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert data["info"]["title"] == "OmniFlow API"

@pytest.mark.asyncio
async def test_docs_route(async_client: AsyncClient):
    """Test that Swagger docs UI is accessible."""
    response = await async_client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text

@pytest.mark.asyncio
async def test_health_route(async_client: AsyncClient):
    """Test the health check endpoint."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_analytics_overview_unauthorized(async_client: AsyncClient):
    """Test analytics route without workspace header requires auth."""
    response = await async_client.get("/api/v1/analytics/overview?period=7d")
    assert response.status_code in [401, 403, 400]

@pytest.mark.asyncio
async def test_workflows_list_unauthorized(async_client: AsyncClient):
    """Test workflows route without auth."""
    response = await async_client.get("/api/v1/workflows/")
    assert response.status_code in [401, 403, 400]

@pytest.mark.asyncio
async def test_analytics_success(async_client: AsyncClient, auth_a):
    """Test analytics overview succeeds with valid auth."""
    headers = {"Authorization": f"Bearer {auth_a.token}", "x-workspace-id": str(auth_a.workspace_id)}
    response = await async_client.get("/api/v1/analytics/overview?period=7d", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_conversations" in data["data"]["kpis"]

@pytest.mark.asyncio
async def test_workflow_crud_and_isolation(async_client: AsyncClient, auth_a, auth_b):
    """Test creating a workflow and ensuring workspace isolation."""
    # User A creates a workflow
    headers_a = {"Authorization": f"Bearer {auth_a.token}", "x-workspace-id": str(auth_a.workspace_id)}
    payload = {"name": "Test Workflow A", "trigger_type": "webhook"}
    resp_create = await async_client.post("/api/v1/workflows/", json=payload, headers=headers_a)
    assert resp_create.status_code == 200
    workflow_id = resp_create.json()["data"]["workflow_id"]
    
    # User A can list it
    resp_list_a = await async_client.get("/api/v1/workflows/", headers=headers_a)
    assert resp_list_a.status_code == 200
    workflows_a = resp_list_a.json()["data"]["workflows"]
    assert len(workflows_a) == 1
    assert workflows_a[0]["name"] == "Test Workflow A"

    # User B cannot see User A's workflow (Workspace Isolation)
    headers_b = {"Authorization": f"Bearer {auth_b.token}", "x-workspace-id": str(auth_b.workspace_id)}
    resp_list_b = await async_client.get("/api/v1/workflows/", headers=headers_b)
    assert resp_list_b.status_code == 200
    workflows_b = resp_list_b.json()["data"]["workflows"]
    assert len(workflows_b) == 0  # Should be empty state

@pytest.mark.asyncio
async def test_knowledge_base_crud(async_client: AsyncClient, auth_a):
    """Test knowledge base empty state, upload, and delete."""
    import unittest.mock
    # Mock BackgroundTasks so the background processor doesn't crash the event loop
    with unittest.mock.patch('fastapi.BackgroundTasks.add_task', return_value=None):
        headers_a = {"Authorization": f"Bearer {auth_a.token}", "x-workspace-id": str(auth_a.workspace_id)}
        
        # Check empty state
        resp_empty = await async_client.get("/api/v1/knowledge/documents", headers=headers_a)
        assert resp_empty.status_code == 200
        assert len(resp_empty.json()["data"]["documents"]) == 0
        
        # Create document
        payload = {"name": "Doc1", "file_type": "text/plain", "file_url": "s3://mock"}
        resp_create = await async_client.post("/api/v1/knowledge/documents", json=payload, headers=headers_a)
        assert resp_create.status_code == 200
        doc_id = resp_create.json()["data"]["document_id"]
        
        # List documents
        resp_list = await async_client.get("/api/v1/knowledge/documents", headers=headers_a)
        assert resp_list.status_code == 200
        assert len(resp_list.json()["data"]["documents"]) == 1
        assert resp_list.json()["data"]["documents"][0] == doc_id
        
        # Get specific document
        resp_get = await async_client.get(f"/api/v1/knowledge/documents/{doc_id}", headers=headers_a)
        assert resp_get.status_code == 200
        assert resp_get.json()["data"]["name"] == "Doc1"
        
        # Delete document
        resp_delete = await async_client.delete(f"/api/v1/knowledge/documents/{doc_id}", headers=headers_a)
        assert resp_delete.status_code == 200
        
        # Verify deletion (empty state)
        resp_empty_after = await async_client.get("/api/v1/knowledge/documents", headers=headers_a)
        assert len(resp_empty_after.json()["data"]["documents"]) == 0

@pytest.mark.asyncio
async def test_workspace_isolation_cross_tenant_access_denied(async_client: AsyncClient, auth_a, auth_b):
    """Test that auth_a cannot access endpoint if they pass auth_b's workspace ID."""
    # Attempting to access Workspace B using User A's token
    headers_cross = {"Authorization": f"Bearer {auth_a.token}", "x-workspace-id": str(auth_b.workspace_id)}
    response = await async_client.get("/api/v1/analytics/overview?period=7d", headers=headers_cross)
    # The middleware should reject this with 401/403 or 400
    assert response.status_code in [401, 403, 400]

@pytest.mark.asyncio
async def test_not_found_behavior(async_client: AsyncClient, auth_a):
    """Test 404 behavior for getting a non-existent document."""
    from uuid import uuid4
    headers_a = {"Authorization": f"Bearer {auth_a.token}", "x-workspace-id": str(auth_a.workspace_id)}
    resp_get = await async_client.get(f"/api/v1/knowledge/documents/{uuid4()}", headers=headers_a)
    assert resp_get.status_code == 404
