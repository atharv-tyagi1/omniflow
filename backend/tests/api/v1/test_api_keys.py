import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.public_api import PublicApiKey, PublicApiKeyAudit, PublicApiKeyScope
from backend.app.models.user import User

@pytest.fixture
async def api_key_setup(db: AsyncSession, auth_a, async_client: AsyncClient):
    from backend.app.services.public.public_api_service import PublicApiService
    from backend.app.models.workspace import Workspace
    
    # Get user
    stmt = select(User).where(User.email == "owner_a@omniflow.ai")
    result = await db.execute(stmt)
    test_user = result.scalars().first()
    
    import uuid
    workspace_id = uuid.UUID(auth_a.workspace_id)

    # Promote workspace to pro plan
    workspace = await db.get(Workspace, workspace_id)
    if workspace:
        workspace.plan = "pro"
        db.add(workspace)
        await db.commit()
    
    # Create initial API key
    plain_key = await PublicApiService.create_api_key(
        db=db,
        workspace_id=workspace_id,
        user_id=test_user.id,
        name="Test API Key",
        scopes=["analytics.read"]
    )
    
    stmt = select(PublicApiKey).where(PublicApiKey.name == "Test API Key")
    result = await db.execute(stmt)
    api_key_record = result.scalars().first()
    
    async_client.headers["Authorization"] = f"Bearer {auth_a.token}"
    
    return {"plain_key": plain_key, "api_key": api_key_record, "workspace_id": workspace_id, "user": test_user}

@pytest.mark.asyncio
async def test_create_api_key(async_client: AsyncClient, api_key_setup):
    resp = await async_client.post("/api/v1/api-keys", json={
        "name": "New API Key",
        "scopes": ["chat.write"]
    })
    
    assert resp.status_code == 200
    data = resp.json()
    assert "key_secret" in data
    assert data["key_secret"].startswith("of_live_")

@pytest.mark.asyncio
async def test_list_api_keys_never_exposes_secret(async_client: AsyncClient, api_key_setup):
    resp = await async_client.get("/api/v1/api-keys")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    
    items = data["items"]
    assert len(items) > 0
    first_item = items[0]
    
    # Ensure sensitive fields are excluded
    assert "key_secret" not in first_item
    assert "last_ip" not in first_item
    assert "last_user_agent" not in first_item
    
    assert first_item["prefix"].startswith("of_live_")
    assert first_item["status"] == "active"
    assert first_item["request_count"] >= 0
    assert "rate_limit_tier" in first_item

@pytest.mark.asyncio
async def test_rotate_api_key_preserves_lineage(async_client: AsyncClient, db: AsyncSession, api_key_setup):
    old_id_uuid = api_key_setup["api_key"].id
    old_id = str(old_id_uuid)
    
    resp = await async_client.post(f"/api/v1/api-keys/{old_id}/rotate", json={"reason": "compromised"})
    assert resp.status_code == 200
    data = resp.json()
    
    assert "new_key_secret" in data
    assert data["new_key_secret"] != api_key_setup["plain_key"]
    
    # Check DB
    await db.refresh(api_key_setup["api_key"])
    assert api_key_setup["api_key"].status == "revoked"
    assert api_key_setup["api_key"].revoked_at is not None
    
    # Check audit lineage
    stmt = select(PublicApiKeyAudit).where(PublicApiKeyAudit.old_api_key_id == old_id_uuid, PublicApiKeyAudit.action == "rotate")
    result = await db.execute(stmt)
    audit = result.scalars().first()
    
    assert audit is not None
    assert audit.reason == "compromised"
    assert audit.new_api_key_id is not None
    
    # Verify new key is active
    stmt = select(PublicApiKey).where(PublicApiKey.id == audit.new_api_key_id)
    result = await db.execute(stmt)
    new_key = result.scalars().first()
    assert new_key.status == "active"

@pytest.mark.asyncio
async def test_soft_revoke_api_key(async_client: AsyncClient, db: AsyncSession, api_key_setup):
    api_key_id_uuid = api_key_setup["api_key"].id
    api_key_id = str(api_key_id_uuid)
    
    # Revoke
    resp = await async_client.delete(f"/api/v1/api-keys/{api_key_id}")
    assert resp.status_code == 200
    
    # Verify soft revoke
    await db.refresh(api_key_setup["api_key"])
    assert api_key_setup["api_key"].status == "revoked"
    assert api_key_setup["api_key"].revoked_at is not None
    
    # Verify idempotent
    resp = await async_client.delete(f"/api/v1/api-keys/{api_key_id}")
    assert resp.status_code == 200

    # Verify audit
    stmt = select(PublicApiKeyAudit).where(PublicApiKeyAudit.api_key_id == api_key_id_uuid, PublicApiKeyAudit.action == "revoke")
    result = await db.execute(stmt)
    audit = result.scalars().first()
    assert audit is not None

@pytest.mark.asyncio
async def test_api_key_pagination_filtering(async_client: AsyncClient, db: AsyncSession, api_key_setup):
    resp = await async_client.get("/api/v1/api-keys?page=1&limit=1&status=active")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert data["limit"] == 1
    assert data["page"] == 1
    assert len(data["items"]) == 1
    
    # Search filter
    resp = await async_client.get("/api/v1/api-keys?search=Test")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) >= 1
    assert "Test" in data["items"][0]["name"]
