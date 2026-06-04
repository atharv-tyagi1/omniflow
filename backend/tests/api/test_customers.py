import pytest
from httpx import AsyncClient
from backend.app.main import app

@pytest.mark.asyncio
async def test_workspace_isolation_customer_creation(
    authorized_client: AsyncClient,
    another_authorized_client: AsyncClient,
    workspace_a,
    workspace_b
):
    """
    Test that creating a customer is isolated to the specific workspace.
    """
    # 1. Create customer in Workspace A
    response_a = await authorized_client.post(
        "/api/v1/customers",
        json={"name": "Alice Corp", "email": "alice@example.com"},
        headers={"X-Workspace-ID": str(workspace_a.id)}
    )
    assert response_a.status_code == 200
    customer_id = response_a.json()["data"]["id"]

    # 2. Try to fetch the customer from Workspace B
    response_b = await another_authorized_client.get(
        f"/api/v1/customers/{customer_id}",
        headers={"X-Workspace-ID": str(workspace_b.id)}
    )
    assert response_b.status_code in [403, 404]

@pytest.mark.asyncio
async def test_workspace_deletion_safety_not_owner(
    authorized_client: AsyncClient,
    workspace_a,
    member_user
):
    """
    Test that a non-owner cannot delete a workspace.
    """
    # Set the client to authenticate as a non-owner (member)
    authorized_client.headers.update({"Authorization": f"Bearer {member_user.token}"})
    
    response = await authorized_client.delete(
        "/api/v1/workspaces/current",
        headers={"X-Workspace-ID": str(workspace_a.id)}
    )
    assert response.status_code == 403 # Caught by `require_admin` middleware
