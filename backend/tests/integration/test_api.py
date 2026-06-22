import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_openapi_route(client):
    """Test that OpenAPI is accessible at the root."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert data["info"]["title"] == "OmniFlow API"

@pytest.mark.asyncio
async def test_docs_route(client):
    """Test that Swagger docs UI is accessible."""
    response = await client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text

@pytest.mark.asyncio
async def test_health_route(client):
    """Test the health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_analytics_overview_unauthorized(client):
    """Test analytics route without workspace header requires auth."""
    response = await client.get("/api/v1/analytics/overview")
    assert response.status_code in [401, 403, 400]

@pytest.mark.asyncio
async def test_workflows_list_unauthorized(client):
    """Test workflows route without auth."""
    response = await client.get("/api/v1/workflows/")
    assert response.status_code in [401, 403, 400]
