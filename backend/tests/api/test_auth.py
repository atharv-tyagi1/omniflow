import pytest
from httpx import AsyncClient

# Test Data
TEST_USER = {
    "email": "test@omniflow.ai",
    "password": "securepassword123",
    "full_name": "Test User",
    "workspace_name": "Test Workspace",
}

@pytest.mark.asyncio
async def test_signup(async_client: AsyncClient):
    response = await async_client.post("/api/v1/auth/signup", json=TEST_USER)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "user" in data["data"]
    assert data["data"]["user"]["email"] == TEST_USER["email"]
    assert data["data"]["user"]["role"] == "owner"  # Creator is owner

@pytest.mark.asyncio
async def test_login(async_client: AsyncClient):
    # First sign up
    await async_client.post("/api/v1/auth/signup", json=TEST_USER)

    # Then login
    login_data = {"email": TEST_USER["email"], "password": TEST_USER["password"]}
    response = await async_client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data["data"]

@pytest.mark.asyncio
async def test_get_me(async_client: AsyncClient):
    # Sign up
    signup_resp = await async_client.post("/api/v1/auth/signup", json=TEST_USER)
    token = signup_resp.json()["data"]["access_token"]

    # Get Me
    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["email"] == TEST_USER["email"]
    assert "workspace_id" in data["data"]
    assert data["data"]["role"] == "owner"
