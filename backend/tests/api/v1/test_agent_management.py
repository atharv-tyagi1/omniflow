"""
Phase 21.2F Tests — Agent Management API
Tests: CRUD, Clone, Archive/Restore, Publish, Workspace Isolation, RBAC
"""
import pytest
import uuid
from httpx import AsyncClient

TEST_USER = {
    "email": "agent_test@omniflow.ai",
    "password": "securepassword123",
    "full_name": "Agent Test User",
    "workspace_name": "Agent Test Workspace",
}

OTHER_USER = {
    "email": "other_workspace@omniflow.ai",
    "password": "securepassword456",
    "full_name": "Other User",
    "workspace_name": "Other Workspace",
}


async def _signup_and_auth(async_client, user_data: dict) -> dict:
    """Helper to sign up and return auth context."""
    resp = await async_client.post("/api/v1/auth/signup", json=user_data)
    assert resp.status_code == 200, f"Signup failed: {resp.text}"
    data = resp.json()["data"]
    return {
        "token": data["access_token"],
        "workspace_id": data["user"]["workspace_id"],
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
    }


def _agent_url(workspace_id: str, suffix: str = "") -> str:
    return f"/api/v1/workspaces/{workspace_id}/agents{suffix}"


@pytest.mark.asyncio
async def test_create_agent(async_client: AsyncClient):
    """Create an agent in a workspace."""
    ctx = await _signup_and_auth(async_client, TEST_USER)
    payload = {"name": "HR Assistant", "category": "hr", "is_active": True}
    resp = await async_client.post(
        _agent_url(ctx["workspace_id"]), json=payload, headers=ctx["headers"]
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "HR Assistant"
    assert data["category"] == "hr"


@pytest.mark.asyncio
async def test_list_agents(async_client: AsyncClient):
    """List agents returns workspace-scoped results."""
    ctx = await _signup_and_auth(async_client, {**TEST_USER, "email": "list_agents@omniflow.ai"})
    # Create two agents
    for name in ["Agent A", "Agent B"]:
        await async_client.post(
            _agent_url(ctx["workspace_id"]),
            json={"name": name, "category": "general", "is_active": True},
            headers=ctx["headers"],
        )
    resp = await async_client.get(_agent_url(ctx["workspace_id"]), headers=ctx["headers"])
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_get_agent_detail(async_client: AsyncClient):
    """Get agent detail includes versions list."""
    ctx = await _signup_and_auth(async_client, {**TEST_USER, "email": "detail_test@omniflow.ai"})
    create = await async_client.post(
        _agent_url(ctx["workspace_id"]),
        json={"name": "Detail Agent", "category": "sales", "is_active": True},
        headers=ctx["headers"],
    )
    agent_id = create.json()["id"]
    resp = await async_client.get(_agent_url(ctx["workspace_id"], f"/{agent_id}"), headers=ctx["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == agent_id
    assert "versions" in data


@pytest.mark.asyncio
async def test_archive_and_restore_agent(async_client: AsyncClient):
    """Archive and restore an agent."""
    ctx = await _signup_and_auth(async_client, {**TEST_USER, "email": "archive_test@omniflow.ai"})
    create = await async_client.post(
        _agent_url(ctx["workspace_id"]),
        json={"name": "Archive Agent", "category": "support", "is_active": True},
        headers=ctx["headers"],
    )
    agent_id = create.json()["id"]

    # Archive
    resp = await async_client.post(
        _agent_url(ctx["workspace_id"], f"/{agent_id}/archive"), headers=ctx["headers"]
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    # Restore
    resp = await async_client.post(
        _agent_url(ctx["workspace_id"], f"/{agent_id}/restore"), headers=ctx["headers"]
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True


@pytest.mark.asyncio
async def test_clone_agent(async_client: AsyncClient):
    """Clone creates a new agent with a different name."""
    ctx = await _signup_and_auth(async_client, {**TEST_USER, "email": "clone_test@omniflow.ai"})
    create = await async_client.post(
        _agent_url(ctx["workspace_id"]),
        json={"name": "Original Agent", "category": "hr", "is_active": True},
        headers=ctx["headers"],
    )
    agent_id = create.json()["id"]

    resp = await async_client.post(
        _agent_url(ctx["workspace_id"], f"/{agent_id}/clone"),
        json={"new_name": "Cloned Agent"},
        headers=ctx["headers"],
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Cloned Agent"
    assert data["id"] != agent_id


@pytest.mark.asyncio
async def test_workspace_isolation(async_client: AsyncClient):
    """Agent from workspace A cannot be accessed from workspace B."""
    ctx_a = await _signup_and_auth(async_client, {**TEST_USER, "email": "ws_a@omniflow.ai"})
    ctx_b = await _signup_and_auth(async_client, {**OTHER_USER, "email": "ws_b@omniflow.ai"})

    # Create in workspace A
    create = await async_client.post(
        _agent_url(ctx_a["workspace_id"]),
        json={"name": "Private Agent", "category": "legal", "is_active": True},
        headers=ctx_a["headers"],
    )
    agent_id = create.json()["id"]

    # Attempt access from workspace B — must return 404 (not 200 or 403)
    resp = await async_client.get(
        _agent_url(ctx_b["workspace_id"], f"/{agent_id}"),
        headers=ctx_b["headers"],
    )
    assert resp.status_code == 404, "Cross-workspace access must be denied with 404"


@pytest.mark.asyncio
async def test_delete_agent(async_client: AsyncClient):
    """Delete an agent returns 204."""
    ctx = await _signup_and_auth(async_client, {**TEST_USER, "email": "delete_test@omniflow.ai"})
    create = await async_client.post(
        _agent_url(ctx["workspace_id"]),
        json={"name": "Delete Me", "category": "general", "is_active": True},
        headers=ctx["headers"],
    )
    agent_id = create.json()["id"]

    resp = await async_client.delete(
        _agent_url(ctx["workspace_id"], f"/{agent_id}"), headers=ctx["headers"]
    )
    assert resp.status_code == 204

    # Confirm it's gone
    resp = await async_client.get(
        _agent_url(ctx["workspace_id"], f"/{agent_id}"), headers=ctx["headers"]
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_version_and_publish(async_client: AsyncClient):
    """Create a version and publish it — subsequent publish is idempotent."""
    ctx = await _signup_and_auth(async_client, {**TEST_USER, "email": "version_test@omniflow.ai"})
    create = await async_client.post(
        _agent_url(ctx["workspace_id"]),
        json={"name": "Version Agent", "category": "finance", "is_active": True},
        headers=ctx["headers"],
    )
    agent_id = create.json()["id"]

    # Create version
    version_resp = await async_client.post(
        _agent_url(ctx["workspace_id"], f"/{agent_id}/versions"),
        json={
            "prompt": {"system_prompt": "You are a finance assistant.", "welcome_prompt": None, "fallback_prompt": None},
            "model": {"provider": "gemini", "model_name": "gemini-2.0-flash", "config": {}},
            "publish": False,
        },
        headers=ctx["headers"],
    )
    assert version_resp.status_code == 201
    version_id = version_resp.json()["id"]

    # Publish
    pub_resp = await async_client.post(
        _agent_url(ctx["workspace_id"], f"/{agent_id}/versions/{version_id}/publish"),
        headers=ctx["headers"],
    )
    assert pub_resp.status_code == 200
    assert pub_resp.json()["is_published"] is True

    # Idempotent re-publish
    pub_resp2 = await async_client.post(
        _agent_url(ctx["workspace_id"], f"/{agent_id}/versions/{version_id}/publish"),
        headers=ctx["headers"],
    )
    assert pub_resp2.status_code == 200
    assert pub_resp2.json()["is_published"] is True


@pytest.mark.asyncio
async def test_sandbox_metadata(async_client: AsyncClient):
    """Sandbox GET returns draft version metadata."""
    ctx = await _signup_and_auth(async_client, {**TEST_USER, "email": "sandbox_test@omniflow.ai"})
    create = await async_client.post(
        _agent_url(ctx["workspace_id"]),
        json={"name": "Sandbox Agent", "category": "general", "is_active": True},
        headers=ctx["headers"],
    )
    agent_id = create.json()["id"]

    resp = await async_client.get(
        _agent_url(ctx["workspace_id"], f"/{agent_id}/sandbox"), headers=ctx["headers"]
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "draft_version_id" in data


@pytest.mark.asyncio
async def test_unauthorized_access_denied(async_client: AsyncClient):
    """No bearer token returns 401."""
    fake_ws = str(uuid.uuid4())
    resp = await async_client.get(_agent_url(fake_ws))
    assert resp.status_code == 401
