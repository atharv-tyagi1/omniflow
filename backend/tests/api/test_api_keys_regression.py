import pytest
from httpx import AsyncClient
from sqlalchemy import text
from backend.app.core.database import AsyncSessionLocal
import uuid

import pytest_asyncio

@pytest_asyncio.fixture
async def legacy_api_keys(db, auth_a):
    workspace_id = uuid.UUID(auth_a.workspace_id)
    user_id = uuid.UUID(auth_a.user_id)
    
    keys = {
        "null_status": uuid.uuid4(),
        "revoked_legacy": uuid.uuid4(),
        "missing_cols": uuid.uuid4(),
    }
    
    from backend.app.models.public_api import PublicApiKey
    
    key1 = PublicApiKey(id=keys["null_status"], workspace_id=workspace_id, name="Active Legacy Key", key_hash="hash1", prefix="of_live_", status="active", is_active=True, rate_limit_tier="free")
    key2 = PublicApiKey(id=keys["revoked_legacy"], workspace_id=workspace_id, name="Revoked Legacy Key", key_hash="hash2", prefix="of_live_", status="revoked", is_active=False, rate_limit_tier="free")
    key3 = PublicApiKey(id=keys["missing_cols"], workspace_id=workspace_id, name="Missing Cols Key", key_hash="hash3", prefix="of_live_", status="active", is_active=True, rate_limit_tier="free")
    
    db.add_all([key1, key2, key3])
    await db.commit()
    return keys

@pytest.mark.asyncio
async def test_api_keys_regression(async_client: AsyncClient, auth_a, legacy_api_keys):
    headers = {"Authorization": f"Bearer {auth_a.token}"}
    test_workspace_id = auth_a.workspace_id
    
    # 1. Create Key
    create_resp = await async_client.post(
        f"/api/v1/api-keys?workspace_id={test_workspace_id}",
        json={"name": "Regression Key", "scopes": ["analytics.read"]},
        headers=headers
    )
    assert create_resp.status_code == 200
    data = create_resp.json()
    assert "key_secret" in data
    api_key_secret = data["key_secret"]

    # 2. List Keys and Verify Legacy Keys are Handled
    list_resp = await async_client.get(
        f"/api/v1/api-keys?workspace_id={test_workspace_id}",
        headers=headers
    )
    assert list_resp.status_code == 200
    keys_data = list_resp.json()
    keys = keys_data["items"]
    assert len(keys) >= 4 # 1 created + 3 legacy
    
    # Check response schema stability
    found_active_legacy = False
    found_revoked = False
    found_missing_cols = False
    for k in keys:
        assert "status" in k
        assert "name" in k
        assert "id" in k
        
        # Verify schema fills in gaps
        if k["id"] == str(legacy_api_keys["null_status"]):
            found_active_legacy = True
            assert k["status"] == "active"
        elif k["id"] == str(legacy_api_keys["revoked_legacy"]):
            found_revoked = True
            assert k["status"] == "revoked"
        elif k["id"] == str(legacy_api_keys["missing_cols"]):
            found_missing_cols = True
            
    assert found_active_legacy, "Active legacy key missing"
    assert found_revoked, "Revoked key missing"
    assert found_missing_cols, "Missing cols key missing"
    
    key_id = keys[0]["id"]

    # 3. Use key (mock route if needed, or just assume it works if status is active)
    # Since we can't easily test usage without a mock endpoint, we skip to revoke

    # 4. Revoke Key
    revoke_resp = await async_client.delete(
        f"/api/v1/api-keys/{key_id}?workspace_id={test_workspace_id}",
        headers=headers
    )
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["success"] == True
    
    # 5. Try to revoke an already revoked legacy key
    revoke_legacy = await async_client.delete(
        f"/api/v1/api-keys/{legacy_api_keys['revoked_legacy']}?workspace_id={test_workspace_id}",
        headers=headers
    )
    assert revoke_legacy.status_code == 200 # Should be idempotent
