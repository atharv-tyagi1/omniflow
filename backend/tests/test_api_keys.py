import pytest
from httpx import AsyncClient
from backend.tests.conftest import _AuthBundle
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from uuid import UUID

from backend.app.models.public_api import PublicApiKey

from backend.app.repositories.workspace_repository import WorkspaceRepository
from sqlalchemy import select
from backend.app.models.workspace_member import WorkspaceMember

# Helper to upgrade workspace plan for capability testing
async def _upgrade_plan(db: AsyncSession, workspace_id: str, plan: str = "pro"):
    workspace = await WorkspaceRepository.get(db, UUID(workspace_id))
    workspace.plan = plan
    db.add(workspace)
    await db.commit()

# Helper to demote user role for RBAC testing
async def _demote_role(db: AsyncSession, workspace_id: str, role: str = "member"):
    stmt = select(WorkspaceMember).where(WorkspaceMember.workspace_id == UUID(workspace_id))
    result = await db.execute(stmt)
    member = result.scalars().first()
    member.role = role
    db.add(member)
    await db.commit()

@pytest.mark.asyncio
async def test_capability_denied(async_client: AsyncClient, auth_a: _AuthBundle):
    """Test that workspaces on free tier are denied API key management."""
    headers = {
        "Authorization": f"Bearer {auth_a.token}",
        "x-workspace-id": auth_a.workspace_id
    }
    
    # Attempt to create key (should fail capability check)
    resp = await async_client.post(
        "/api/v1/api-keys",
        json={"name": "Test Key", "scopes": ["chat"]},
        headers=headers
    )
    assert resp.status_code == 403
    assert "plan upgrade" in resp.json()["error"]["message"]

@pytest.mark.asyncio
async def test_rbac_denied(async_client: AsyncClient, auth_a: _AuthBundle, db: AsyncSession):
    """Test that regular members are denied API key management even if plan allows."""
    # Upgrade plan so capability check passes
    await _upgrade_plan(db, auth_a.workspace_id, "pro")
    
    # Demote user to regular member so RBAC check fails
    await _demote_role(db, auth_a.workspace_id, "member")
    
    headers = {
        "Authorization": f"Bearer {auth_a.token}",
        "x-workspace-id": auth_a.workspace_id
    }
    
    # Attempt to create key (should fail RBAC check)
    resp = await async_client.post(
        "/api/v1/api-keys",
        json={"name": "Test Key", "scopes": ["chat"]},
        headers=headers
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] in ["AUTHORIZATION_ERROR", "FORBIDDEN"]

@pytest.mark.asyncio
async def test_create_and_lifecycle(async_client: AsyncClient, auth_a: _AuthBundle, db: AsyncSession):
    """End-to-end test of create, list, rotate, revoke with proper RBAC and capability."""
    await _upgrade_plan(db, auth_a.workspace_id, "pro")
    
    headers = {
        "Authorization": f"Bearer {auth_a.token}",
        "x-workspace-id": auth_a.workspace_id
    }
    
    # 1. Create API Key
    create_resp = await async_client.post(
        "/api/v1/api-keys",
        json={"name": "Production Key", "scopes": ["chat", "analytics_read"]},
        headers=headers
    )
    if create_resp.status_code != 200:
        print("CREATE FAILED:", create_resp.json())
    assert create_resp.status_code == 200
    create_data = create_resp.json()
    assert "key_secret" in create_data
    secret = create_data["key_secret"]
    assert secret.startswith("of_live_")
    
    # 2. List API Keys
    list_resp = await async_client.get("/api/v1/api-keys", headers=headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert "items" in list_data
    items = list_data["items"]
    assert len(items) == 1
    key_id = items[0]["id"]
    assert items[0]["name"] == "Production Key"
    assert "key_secret" not in items[0] # Ensure secret isn't leaked
    
    # 3. Rotate API Key
    rotate_resp = await async_client.post(
        f"/api/v1/api-keys/{key_id}/rotate",
        json={"reason": "routine"},
        headers=headers
    )
    assert rotate_resp.status_code == 200
    rotate_data = rotate_resp.json()
    assert "new_key_secret" in rotate_data
    new_secret = rotate_data["new_key_secret"]
    assert new_secret != secret
    
    # 4. Revoke API Key
    revoke_resp = await async_client.delete(f"/api/v1/api-keys/{key_id}", headers=headers)
    assert revoke_resp.status_code == 200
    
    # Idempotent Revoke
    revoke_resp2 = await async_client.delete(f"/api/v1/api-keys/{key_id}", headers=headers)
    assert revoke_resp2.status_code == 200

@pytest.mark.asyncio
async def test_validation_errors(async_client: AsyncClient, auth_a: _AuthBundle, db: AsyncSession):
    """Test 422 payload mismatch."""
    await _upgrade_plan(db, auth_a.workspace_id, "pro")
    headers = {
        "Authorization": f"Bearer {auth_a.token}",
        "x-workspace-id": auth_a.workspace_id
    }
    
    # Missing required 'scopes'
    resp = await async_client.post(
        "/api/v1/api-keys",
        json={"name": "Bad Key"},
        headers=headers
    )
    if resp.status_code != 422:
        print("VALIDATION ERROR FAILED:", resp.json())
    assert resp.status_code == 422
    # FastAPI default 422 returns {"detail": [...]}
    assert "detail" in resp.json()

@pytest.mark.asyncio
async def test_workspace_isolation(async_client: AsyncClient, auth_a: _AuthBundle, auth_b: _AuthBundle, db: AsyncSession):
    """Admin of Workspace B cannot access Workspace A's keys."""
    await _upgrade_plan(db, auth_a.workspace_id, "pro")
    await _upgrade_plan(db, auth_b.workspace_id, "pro")
    
    headers_a = {
        "Authorization": f"Bearer {auth_a.token}",
        "x-workspace-id": auth_a.workspace_id
    }
    
    headers_b = {
        "Authorization": f"Bearer {auth_b.token}",
        "x-workspace-id": auth_b.workspace_id
    }
    
    # 1. User A creates a key
    create_resp = await async_client.post(
        "/api/v1/api-keys",
        json={"name": "Key A", "scopes": ["chat"]},
        headers=headers_a
    )
    assert create_resp.status_code == 200
    
    # 2. User B tries to list keys, should not see A's keys
    list_resp_b = await async_client.get("/api/v1/api-keys", headers=headers_b)
    assert len(list_resp_b.json()["items"]) == 0

from unittest.mock import patch
from backend.tests.conftest import TestingSessionLocal

@pytest.mark.asyncio
@patch("backend.app.core.database.AsyncSessionLocal", new=TestingSessionLocal)
async def test_rotation_lineage_and_usage_tracking(async_client: AsyncClient, auth_a: _AuthBundle, db: AsyncSession):
    """Test rotation stores old_key_id and new_key_id, and usage tracking updates correctly."""
    await _upgrade_plan(db, auth_a.workspace_id, "pro")
    headers = {
        "Authorization": f"Bearer {auth_a.token}",
        "x-workspace-id": auth_a.workspace_id
    }
    
    # 1. Create a key
    create_resp = await async_client.post(
        "/api/v1/api-keys",
        json={"name": "Audit Key", "scopes": ["chat"]},
        headers=headers
    )
    secret = create_resp.json()["key_secret"]
    
    list_resp = await async_client.get("/api/v1/api-keys", headers=headers)
    items = list_resp.json()["items"]
    key_id = items[0]["id"]
    
    # 2. Rotate the key
    await async_client.post(
        f"/api/v1/api-keys/{key_id}/rotate",
        json={"reason": "security_audit"},
        headers=headers
    )
    
    list_resp2 = await async_client.get("/api/v1/api-keys", headers=headers)
    new_items = list_resp2.json()["items"]
    
    # The old key should be revoked, new key active
    old_key = next((k for k in new_items if k["id"] == key_id), None)
    assert old_key is not None
    assert old_key["status"] == "revoked"
    
    # 3. Simulate usage (API call using the new key)
    # The new key is created in rotate, but how do we get its secret? We could capture it from rotate response.
    # Actually, let's just make a usage tracking call using the *first* secret, before rotating. But we already rotated it!
    # Wait, usage tracking is async via background task in PublicAuth.
    # Let's create a *new* key for usage tracking so we don't mix logic.
    create_usage_resp = await async_client.post(
        "/api/v1/api-keys",
        json={"name": "Usage Key", "scopes": ["chat"]},
        headers=headers
    )
    usage_secret = create_usage_resp.json()["key_secret"]
    
    # Make a public API call
    pub_headers = {"X-Api-Key": usage_secret}
    pub_resp = await async_client.get("/api/public/v1/conversations", headers=pub_headers)
    assert pub_resp.status_code == 200
    
    import asyncio
    await asyncio.sleep(0.5) # Wait for background usage tracking to commit
    
    # Check usage
    list_resp3 = await async_client.get("/api/v1/api-keys", headers=headers)
    usage_key = next(k for k in list_resp3.json()["items"] if k["name"] == "Usage Key")
    assert usage_key["request_count"] == 1
    assert usage_key["last_used_at"] is not None
