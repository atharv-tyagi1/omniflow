import asyncio
import httpx
from backend.app.main import app

async def test_failover():
    print("[FAILOVER AND IDEMPOTENCY TEST]")
    
    # Mock dispatch to throw a transient error
    import backend.app.api.public.v1.agents
    async def mock_fail_dispatch(*args, **kwargs):
        raise Exception("Simulated transient LLM outage")
    backend.app.api.public.v1.agents.AgentService.dispatch = mock_fail_dispatch
    
    # 1. Setup isolated tenant via APIs
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        import uuid
        email = f"failover_{uuid.uuid4()}@test.com"
        r_tenant = await client.post("/api/v1/auth/signup", json={
            "email": email, "password": "password123", "full_name": "Test", "workspace_name": "Test Workspace"
        })
        import jwt
        print(f"Tenant JSON: {r_tenant.text}")
        token = r_tenant.json()["data"]["access_token"]
        payload = jwt.decode(token, options={"verify_signature": False})
        workspace_id = payload["workspace_id"]
        
        h = {"Authorization": f"Bearer {token}"}
        
        r_agent = await client.post(
            f"/api/v1/workspaces/{workspace_id}/agents",
            headers=h,
            json={"name": "Test Agent", "category": "test", "is_public": True}
        )
        agent_id = r_agent.json()["id"]
        
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/agents/{agent_id}/versions",
            headers=h,
            json={"system_prompt": "You are a test."}
        )
        
        r_key = await client.post(
            f"/api/v1/api-keys",
            headers=h,
            json={"name": "test key", "scopes": ["agent_chat"]}
        )
        key_secret = r_key.json()["key_secret"]
        
        # Test forced error and fail-closed behavior
        print("  Sending request that will fail...")
        headers = {
            "X-Api-Key": key_secret,
            "idempotency-key": "test_idem_failover"
        }
        
        r1 = await client.post(
            f"/api/public/v1/agents/{agent_id}/chat",
            headers=headers,
            json={"message": "hello", "stream": False}
        )
        
        if r1.status_code == 500 and "INTERNAL_ERROR" in r1.text:
            print("  [PASS] Request hard-failed with 500 (Fail-Closed)")
        else:
            print(f"  [FAIL] Expected 500, got {r1.status_code}")
            
        # Verify idempotency key was rolled back (status="failed") by retrying
        # The retry should NOT return 400 PREVIOUS_REQUEST_FAILED, it should just attempt execution again (and fail again with 500)
        print("  Retrying the failed request...")
        r2 = await client.post(
            f"/api/public/v1/agents/{agent_id}/chat",
            headers=headers,
            json={"message": "hello", "stream": False}
        )
        
        if r2.status_code == 500 and "INTERNAL_ERROR" in r2.text:
            print("  [PASS] Idempotency rollback verified (Retry allowed, didn't block with 400)")
        elif r2.status_code == 400 and "PREVIOUS_REQUEST_FAILED" in r2.text:
            print(f"  [FAIL] Idempotency key was locked in failed state!")
        else:
            print(f"  [FAIL] Expected 500 on retry, got {r2.status_code}")

if __name__ == "__main__":
    asyncio.run(test_failover())
