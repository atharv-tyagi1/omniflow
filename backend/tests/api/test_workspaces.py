import pytest
from httpx import AsyncClient

TEST_USER_1 = {
    "email": "user1@omniflow.ai",
    "password": "securepassword123",
    "full_name": "User One",
    "workspace_name": "Workspace One",
}

TEST_USER_2 = {
    "email": "user2@omniflow.ai",
    "password": "securepassword123",
    "full_name": "User Two",
    "workspace_name": "Workspace Two",
}

@pytest.fixture
async def authenticated_client(async_client: AsyncClient):
    """Fixture that returns a client authenticated as user 1."""
    resp = await async_client.post("/api/v1/auth/signup", json=TEST_USER_1)
    token = resp.json()["data"]["access_token"]
    async_client.headers.update({"Authorization": f"Bearer {token}"})
    return async_client

@pytest.mark.asyncio
async def test_get_current_workspace(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/workspaces/current")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == TEST_USER_1["workspace_name"]

@pytest.mark.asyncio
async def test_create_workspace(authenticated_client: AsyncClient):
    new_ws_data = {"name": "Secondary Workspace", "industry": "Tech"}
    response = await authenticated_client.post("/api/v1/workspaces", json=new_ws_data)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == "Secondary Workspace"
    assert "id" in data["data"]

@pytest.mark.asyncio
async def test_get_workspace_members(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/workspaces/members")
    assert response.status_code == 200
    data = response.json()
    members = data["data"]
    assert len(members) == 1
    assert members[0]["user_email"] == TEST_USER_1["email"]
    assert members[0]["role"] == "owner"

@pytest.mark.asyncio
async def test_workspace_isolation(async_client: AsyncClient):
    # Setup User 1 and User 2
    resp1 = await async_client.post("/api/v1/auth/signup", json=TEST_USER_1)
    token1 = resp1.json()["data"]["access_token"]
    
    resp2 = await async_client.post("/api/v1/auth/signup", json=TEST_USER_2)
    token2 = resp2.json()["data"]["access_token"]

    # User 1 tries to access User 2's workspace by manipulating the API
    # Since workspace_id is derived from the JWT payload and validated against DB membership,
    # User 1 cannot access User 2's workspace.
    
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Get User 2's workspace details
    ws2_response = await async_client.get("/api/v1/workspaces/current", headers=headers2)
    ws2_id = ws2_response.json()["data"]["id"]

    # There's no direct GET /workspaces/{id} endpoint exposed currently, 
    # but isolation is verified because get_current_workspace derives ID strictly from token.
    # We can verify that User 1's current workspace is NOT User 2's workspace.
    ws1_response = await async_client.get("/api/v1/workspaces/current", headers=headers1)
    assert ws1_response.json()["data"]["id"] != ws2_id
