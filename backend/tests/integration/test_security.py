import pytest
from httpx import AsyncClient
from uuid import uuid4, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.security import create_access_token, hash_password
from backend.app.models.user import User
from backend.app.models.workspace import Workspace
from backend.app.models.workspace_member import WorkspaceMember
from backend.app.models.customer import Customer
from backend.app.models.conversation import Conversation
from backend.app.models.workflow import Workflow
from backend.app.models.public_api import PublicApiKey
from backend.app.models.analytics import AnalyticsDailyRollup
from backend.app.repositories.workspace_repository import WorkspaceRepository
from datetime import datetime, timezone

# Helper to create workspace, users and membership roles
async def setup_workspace_user(db: AsyncSession, email: str, role: str, ws_name: str) -> dict:
    workspace = Workspace(id=uuid4(), name=ws_name, plan="pro")
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)

    user = User(
        id=uuid4(),
        email=email,
        full_name=f"Test {role.capitalize()}",
        password_hash=hash_password("securepassword123"),
        status="active"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    member = WorkspaceMember(
        id=uuid4(),
        workspace_id=workspace.id,
        user_id=user.id,
        role=role
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    token_data = {
        "sub": str(user.id),
        "workspace_id": str(workspace.id),
        "role": role,
    }
    token = create_access_token(token_data)
    
    return {
        "user": user,
        "workspace": workspace,
        "member": member,
        "token": token
    }

async def add_member_to_workspace(db: AsyncSession, workspace: Workspace, email: str, role: str) -> dict:
    user = User(
        id=uuid4(),
        email=email,
        full_name=f"Added {role.capitalize()}",
        password_hash=hash_password("securepassword123"),
        status="active"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    member = WorkspaceMember(
        id=uuid4(),
        workspace_id=workspace.id,
        user_id=user.id,
        role=role
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    token_data = {
        "sub": str(user.id),
        "workspace_id": str(workspace.id),
        "role": role,
    }
    token = create_access_token(token_data)

    return {
        "user": user,
        "member": member,
        "token": token
    }

# ===========================================================================
# SECTION 1 – WORKSPACE ISOLATION AUDIT
# ===========================================================================
@pytest.mark.asyncio
async def test_workspace_isolation_matrix(async_client: AsyncClient, db: AsyncSession):
    # Setup Workspace A
    wa_owner = await setup_workspace_user(db, "a1@example.com", "owner", "Workspace A")
    wa_member = await add_member_to_workspace(db, wa_owner["workspace"], "a2@example.com", "member")
    
    # Setup Workspace B
    wb_owner = await setup_workspace_user(db, "b1@example.com", "owner", "Workspace B")
    wb_member = await add_member_to_workspace(db, wb_owner["workspace"], "b2@example.com", "member")

    ws_a_id = str(wa_owner["workspace"].id)
    ws_b_id = str(wb_owner["workspace"].id)

    # 1. A1 accesses Workspace A (Expected: Allowed)
    resp = await async_client.get(
        "/api/v1/workspaces/current",
        headers={"Authorization": f"Bearer {wa_owner['token']}", "x-workspace-id": ws_a_id}
    )
    assert resp.status_code == 200

    # 2. A2 accesses Workspace A (Expected: Allowed)
    resp = await async_client.get(
        "/api/v1/workspaces/current",
        headers={"Authorization": f"Bearer {wa_member['token']}", "x-workspace-id": ws_a_id}
    )
    assert resp.status_code == 200

    # 3. B1 accesses Workspace B (Expected: Allowed)
    resp = await async_client.get(
        "/api/v1/workspaces/current",
        headers={"Authorization": f"Bearer {wb_owner['token']}", "x-workspace-id": ws_b_id}
    )
    assert resp.status_code == 200

    # 4. B2 accesses Workspace B (Expected: Allowed)
    resp = await async_client.get(
        "/api/v1/workspaces/current",
        headers={"Authorization": f"Bearer {wb_member['token']}", "x-workspace-id": ws_b_id}
    )
    assert resp.status_code == 200

    # 5. A1 attempts Workspace B (Expected: Denied)
    resp = await async_client.get(
        "/api/v1/workspaces/current",
        headers={"Authorization": f"Bearer {wa_owner['token']}", "x-workspace-id": ws_b_id}
    )
    assert resp.status_code in [401, 403, 400]

    # 6. A2 attempts Workspace B (Expected: Denied)
    resp = await async_client.get(
        "/api/v1/workspaces/current",
        headers={"Authorization": f"Bearer {wa_member['token']}", "x-workspace-id": ws_b_id}
    )
    assert resp.status_code in [401, 403, 400]

    # 7. B1 attempts Workspace A (Expected: Denied)
    resp = await async_client.get(
        "/api/v1/workspaces/current",
        headers={"Authorization": f"Bearer {wb_owner['token']}", "x-workspace-id": ws_a_id}
    )
    assert resp.status_code in [401, 403, 400]

    # 8. B2 attempts Workspace A (Expected: Denied)
    resp = await async_client.get(
        "/api/v1/workspaces/current",
        headers={"Authorization": f"Bearer {wb_member['token']}", "x-workspace-id": ws_a_id}
    )
    assert resp.status_code in [401, 403, 400]


# ===========================================================================
# SECTION 2 – HEADER SPOOFING AUDIT
# ===========================================================================
@pytest.mark.asyncio
async def test_header_spoofing(async_client: AsyncClient, db: AsyncSession):
    setup = await setup_workspace_user(db, "spoof@example.com", "owner", "Workspace S")
    valid_jwt = setup["token"]
    foreign_ws = str(uuid4())

    # Valid JWT + Invalid Workspace Header (random gibberish)
    resp1 = await async_client.get(
        "/api/v1/workspaces/current",
        headers={"Authorization": f"Bearer {valid_jwt}", "x-workspace-id": "not-a-uuid"}
    )
    assert resp1.status_code in [400, 401, 403, 422, 500]
    assert resp1.status_code != 200

    # Valid JWT + Foreign Workspace Header (correct format but belongs to another workspace)
    resp2 = await async_client.get(
        "/api/v1/workspaces/current",
        headers={"Authorization": f"Bearer {valid_jwt}", "x-workspace-id": foreign_ws}
    )
    assert resp2.status_code in [401, 403, 400]
    assert resp2.status_code != 200

    # Valid JWT + Random Workspace Header (empty/missing header, fallback to JWT claims)
    # Since fallback to JWT claims is expected to use the correct workspace_id embedded in the token,
    # let's verify that omitting x-workspace-id returns 200 (since the JWT contains the correct WS ID).
    resp3 = await async_client.get(
        "/api/v1/workspaces/current",
        headers={"Authorization": f"Bearer {valid_jwt}"}
    )
    assert resp3.status_code == 200


# ===========================================================================
# SECTION 3 – ROLE AUTHORIZATION AUDIT (RBAC)
# ===========================================================================
@pytest.mark.asyncio
async def test_role_authorization_matrix(async_client: AsyncClient, db: AsyncSession):
    ws_setup = await setup_workspace_user(db, "owner@rbac.com", "owner", "RBAC Workspace")
    workspace = ws_setup["workspace"]
    
    admin_setup = await add_member_to_workspace(db, workspace, "admin@rbac.com", "admin")
    member_setup = await add_member_to_workspace(db, workspace, "member@rbac.com", "member")
    
    ws_id = str(workspace.id)

    # A. API Key Management (Requires Admin/Owner)
    # 1. Owner can create API Key
    resp_key_owner = await async_client.post(
        "/api/v1/api-keys",
        json={"name": "Owner Key", "scopes": ["chat"]},
        headers={"Authorization": f"Bearer {ws_setup['token']}", "x-workspace-id": ws_id}
    )
    assert resp_key_owner.status_code == 200

    # 2. Admin can create API Key
    resp_key_admin = await async_client.post(
        "/api/v1/api-keys",
        json={"name": "Admin Key", "scopes": ["chat"]},
        headers={"Authorization": f"Bearer {admin_setup['token']}", "x-workspace-id": ws_id}
    )
    assert resp_key_admin.status_code == 200

    # 3. Member is denied API Key creation
    resp_key_member = await async_client.post(
        "/api/v1/api-keys",
        json={"name": "Member Key", "scopes": ["chat"]},
        headers={"Authorization": f"Bearer {member_setup['token']}", "x-workspace-id": ws_id}
    )
    assert resp_key_member.status_code == 403

    # B. Workspace settings update (Requires Admin/Owner)
    # 1. Member update settings is denied
    resp_update_member = await async_client.put(
        "/api/v1/workspaces/current",
        json={"name": "New Name By Member"},
        headers={"Authorization": f"Bearer {member_setup['token']}", "x-workspace-id": ws_id}
    )
    assert resp_update_member.status_code == 403

    # 2. Admin update settings is allowed
    resp_update_admin = await async_client.put(
        "/api/v1/workspaces/current",
        json={"name": "New Name By Admin"},
        headers={"Authorization": f"Bearer {admin_setup['token']}", "x-workspace-id": ws_id}
    )
    assert resp_update_admin.status_code == 200

    # C. Read access (Allowed for all roles)
    for token in [ws_setup['token'], admin_setup['token'], member_setup['token']]:
        resp = await async_client.get(
            "/api/v1/workspaces/current",
            headers={"Authorization": f"Bearer {token}", "x-workspace-id": ws_id}
        )
        assert resp.status_code == 200


# ===========================================================================
# SECTION 4 – REMOVED MEMBER AUDIT
# ===========================================================================
@pytest.mark.asyncio
async def test_removed_member_jwt_abuse(async_client: AsyncClient, db: AsyncSession):
    ws_setup = await setup_workspace_user(db, "owner_rm@example.com", "owner", "RM Workspace")
    workspace = ws_setup["workspace"]
    
    member_setup = await add_member_to_workspace(db, workspace, "member_rm@example.com", "member")
    
    ws_id = str(workspace.id)
    old_jwt = member_setup["token"]

    # Verify initial access is allowed
    resp_init = await async_client.get(
        "/api/v1/workspaces/current",
        headers={"Authorization": f"Bearer {old_jwt}", "x-workspace-id": ws_id}
    )
    assert resp_init.status_code == 200

    # Delete the workspace membership row for this member
    await db.delete(member_setup["member"])
    await db.commit()

    # Verify access is now rejected across all components with old JWT
    # 1. Workspace API Access
    resp = await async_client.get(
        "/api/v1/workspaces/current",
        headers={"Authorization": f"Bearer {old_jwt}", "x-workspace-id": ws_id}
    )
    assert resp.status_code in [401, 403]

    # 2. Analytics Access
    resp = await async_client.get(
        "/api/v1/analytics/overview?period=7d",
        headers={"Authorization": f"Bearer {old_jwt}", "x-workspace-id": ws_id}
    )
    assert resp.status_code in [401, 403]

    # 3. Workflows Access
    resp = await async_client.get(
        "/api/v1/workflows/",
        headers={"Authorization": f"Bearer {old_jwt}", "x-workspace-id": ws_id}
    )
    assert resp.status_code in [401, 403]

    # 4. Conversations Access
    resp = await async_client.get(
        "/api/v1/conversations/",
        headers={"Authorization": f"Bearer {old_jwt}", "x-workspace-id": ws_id}
    )
    assert resp.status_code in [401, 403]

    # 5. Customers Access
    resp = await async_client.get(
        "/api/v1/customers",
        headers={"Authorization": f"Bearer {old_jwt}", "x-workspace-id": ws_id}
    )
    assert resp.status_code in [401, 403]


# ===========================================================================
# SECTIONS 5–9 – DATA LEAKAGE AUDIT FOR SPECIFIC COMPONENTS
# ===========================================================================
@pytest.mark.asyncio
async def test_data_leakage_isolation(async_client: AsyncClient, db: AsyncSession):
    ws_a = await setup_workspace_user(db, "owner_a@leak.com", "owner", "Leak Workspace A")
    ws_b = await setup_workspace_user(db, "owner_b@leak.com", "owner", "Leak Workspace B")

    ws_a_id = str(ws_a["workspace"].id)
    ws_b_id = str(ws_b["workspace"].id)

    headers_a = {"Authorization": f"Bearer {ws_a['token']}", "x-workspace-id": ws_a_id}
    headers_b = {"Authorization": f"Bearer {ws_b['token']}", "x-workspace-id": ws_b_id}

    # -------------------------------------------------------------
    # 5. Analytics Isolation
    # -------------------------------------------------------------
    # Setup some test data in A (conversations count as analytics metrics)
    cust_a = Customer(id=uuid4(), workspace_id=ws_a["workspace"].id, name="Customer A")
    db.add(cust_a)
    await db.commit()
    
    conv_a = Conversation(id=uuid4(), workspace_id=ws_a["workspace"].id, customer_id=cust_a.id, channel="web")
    db.add(conv_a)
    
    # Create rollup record so it counts in overview query
    rollup_a = AnalyticsDailyRollup(
        workspace_id=ws_a["workspace"].id,
        time_bucket=datetime.now(timezone.utc),
        metric_name="total_conversations",
        value=1
    )
    db.add(rollup_a)
    await db.commit()

    # Query Workspace A overview
    resp_a = await async_client.get("/api/v1/analytics/overview?period=7d", headers=headers_a)
    assert resp_a.status_code == 200
    assert resp_a.json()["data"]["kpis"]["total_conversations"]["value"] == 1

    # Query Workspace B overview (should be 0 or empty)
    resp_b = await async_client.get("/api/v1/analytics/overview?period=7d", headers=headers_b)
    assert resp_b.status_code == 200
    assert resp_b.json()["data"]["kpis"]["total_conversations"]["value"] == 0

    # -------------------------------------------------------------
    # 6. Conversation Isolation
    # -------------------------------------------------------------
    # List conversations for Workspace B (should not include A's)
    resp_conv_b = await async_client.get("/api/v1/conversations/", headers=headers_b)
    assert resp_conv_b.status_code == 200
    assert len(resp_conv_b.json()["data"]["conversations"]) == 0

    # Get conversation details of A from Workspace B context -> Denied/404
    resp_conv_detail = await async_client.get(f"/api/v1/conversations/{conv_a.id}", headers=headers_b)
    assert resp_conv_detail.status_code == 404

    # -------------------------------------------------------------
    # 7. Customer Isolation
    # -------------------------------------------------------------
    # List customers for Workspace B (should not include A's)
    resp_cust_b = await async_client.get("/api/v1/customers", headers=headers_b)
    assert resp_cust_b.status_code == 200
    assert len(resp_cust_b.json()["data"]) == 0

    # Get customer details of A from Workspace B context -> Denied/404
    resp_cust_detail = await async_client.get(f"/api/v1/customers/{cust_a.id}", headers=headers_b)
    assert resp_cust_detail.status_code == 404

    # -------------------------------------------------------------
    # 8. Workflow Isolation
    # -------------------------------------------------------------
    workflow_a = Workflow(id=uuid4(), workspace_id=ws_a["workspace"].id, name="Workflow A", trigger_type="webhook")
    db.add(workflow_a)
    await db.commit()

    # List workflows for Workspace B
    resp_wf_b = await async_client.get("/api/v1/workflows/", headers=headers_b)
    assert resp_wf_b.status_code == 200
    assert len(resp_wf_b.json()["data"]["workflows"]) == 0

    # Trigger workflow of A from Workspace B -> Denied/404
    resp_wf_trigger = await async_client.post(f"/api/v1/workflows/{workflow_a.id}/trigger", headers=headers_b)
    assert resp_wf_trigger.status_code in [400, 404]

    # -------------------------------------------------------------
    # 9. API Key Security
    # -------------------------------------------------------------
    # Create API key in Workspace A
    create_key_resp = await async_client.post(
        "/api/v1/api-keys",
        json={"name": "Key A", "scopes": ["chat"]},
        headers=headers_a
    )
    assert create_key_resp.status_code == 200
    key_secret = create_key_resp.json()["key_secret"]
    
    # Get the key record ID to test management operations
    list_keys_resp = await async_client.get("/api/v1/api-keys", headers=headers_a)
    key_id = list_keys_resp.json()["items"][0]["id"]

    # Attempt to use key in Workspace B request via Public API
    pub_headers = {"X-Api-Key": key_secret, "Idempotency-Key": str(uuid4())}
    # This public call is allowed for Workspace A, but if we query Workspace B conversations it should be empty
    pub_resp = await async_client.get("/api/public/v1/conversations", headers={"X-Api-Key": key_secret})
    assert pub_resp.status_code == 200
    # The conversations returned belong to Workspace A. If we try to query or access Workspace B details via this key, it should reject or isolate
    # For example, sending a chat message using A's key will only create a customer in Workspace A
    chat_payload = {
        "external_customer_id": "cust_leak",
        "customer_name": "Leak User",
        "message": "Hello isolation test",
    }
    chat_resp = await async_client.post("/api/public/v1/chat", json=chat_payload, headers=pub_headers)
    assert chat_resp.status_code == 200
    
    # Confirm the customer was created in Workspace A, not Workspace B
    res_a = await async_client.get("/api/v1/customers", headers=headers_a)
    assert any(c["name"] == "Leak User" for c in res_a.json()["data"])
    res_b = await async_client.get("/api/v1/customers", headers=headers_b)
    assert not any(c["name"] == "Leak User" for c in res_b.json()["data"])

    # Attempt lookup of Workspace A key from Workspace B
    resp_lookup = await async_client.get("/api/v1/api-keys", headers=headers_b)
    assert resp_lookup.status_code == 200
    assert len(resp_lookup.json()["items"]) == 0

    # Attempt deletion/revocation of Workspace A key from Workspace B -> returns 200 (idempotent design) but does not affect A's key
    resp_delete_key = await async_client.delete(f"/api/v1/api-keys/{key_id}", headers=headers_b)
    assert resp_delete_key.status_code in [200, 404, 400]

    # Verify that the key in Workspace A is still active and was NOT deleted
    list_keys_resp_a = await async_client.get("/api/v1/api-keys", headers=headers_a)
    key_a_record = list_keys_resp_a.json()["items"][0]
    assert key_a_record["status"] == "active"
