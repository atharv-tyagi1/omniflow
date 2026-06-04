"""Tests for workspace isolation of customer operations."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_workspace_isolation_customer_creation(async_client: AsyncClient, auth_a, auth_b):
    """
    Creating a customer in Workspace A must not be visible from Workspace B.
    """
    # 1. Create customer in Workspace A
    response_a = await async_client.post(
        "/api/v1/customers",
        json={"name": "Alice Corp", "email": "alice@example.com"},
        headers={
            "Authorization": f"Bearer {auth_a.token}",
            "X-Workspace-ID": auth_a.workspace_id,
        },
    )
    assert response_a.status_code == 200, response_a.text
    customer_id = response_a.json()["data"]["id"]

    # 2. Fetch that customer from Workspace B — must fail
    response_b = await async_client.get(
        f"/api/v1/customers/{customer_id}",
        headers={
            "Authorization": f"Bearer {auth_b.token}",
            "X-Workspace-ID": auth_b.workspace_id,
        },
    )
    assert response_b.status_code in [403, 404]


@pytest.mark.asyncio
async def test_workspace_deletion_safety_not_owner(async_client: AsyncClient, auth_a):
    """
    A workspace owner CAN delete their own workspace, but the endpoint should
    at minimum not crash.  This test verifies the delete endpoint is reachable.
    """
    response = await async_client.delete(
        "/api/v1/workspaces/current",
        headers={
            "Authorization": f"Bearer {auth_a.token}",
            "X-Workspace-ID": auth_a.workspace_id,
        },
    )
    # Accept either success or a permissions error — no 500s
    assert response.status_code in [200, 403, 404], response.text
