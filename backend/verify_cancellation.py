import asyncio
import httpx
import uuid
import jwt
from backend.app.main import app

async def test_cancellation():
    print("[STREAM CANCELLATION AUDIT TEST]")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Setup tenant
        email = f"cancel_{uuid.uuid4()}@test.com"
        r_tenant = await client.post("/api/v1/auth/signup", json={
            "email": email, "password": "password123", "full_name": "Test Cancel", "workspace_name": "Test Workspace"
        })
        token = r_tenant.json()["data"]["access_token"]
        payload = jwt.decode(token, options={"verify_signature": False})
        workspace_id = payload["workspace_id"]
        
        h = {"Authorization": f"Bearer {token}"}
        
        # Create agent
        r_agent = await client.post(
            f"/api/v1/workspaces/{workspace_id}/agents",
            headers=h,
            json={"name": "Cancel Test", "category": "test", "is_public": True}
        )
        agent_id = r_agent.json()["id"]
        
        # Mock LLM dispatch to sleep so we can cancel it
        import backend.app.api.public.v1.agents
        async def mock_slow_dispatch(*args, **kwargs):
            await asyncio.sleep(5.0) # sleep 5s
            return {"content": "mocked", "status": "success", "run_id": "123", "latency_ms": 10, "tokens_used": 100}
        backend.app.api.public.v1.agents.AgentService.dispatch = mock_slow_dispatch
        
        r_key = await client.post(
            f"/api/v1/api-keys",
            headers=h,
            json={"name": "test key", "scopes": ["agent_chat"]}
        )
        key_secret = r_key.json()["key_secret"]
        
        print("  Starting stream request...")
        headers = {"X-Api-Key": key_secret}
        
        # We start the stream, wait 1 second, then cancel the task/timeout to simulate client disconnect
        try:
            async with client.stream(
                "POST", 
                f"/api/public/v1/agents/{agent_id}/chat/stream", 
                headers=headers, 
                json={"message": "hello", "stream": True}
            ) as response:
                async for line in response.aiter_lines():
                    print(f"  Received: {line}")
                    if "event: start" in line:
                        break # Got the start event
                
                print("  Simulating abrupt client disconnect...")
                # By exiting the context manager abruptly, it closes the connection
        except Exception as e:
            print(f"  Disconnect error: {e}")
            
        print("  Waiting 2s for server to process cancellation...")
        await asyncio.sleep(2)
        
        # Verify the audit log exists in the DB!
        from backend.app.core.database import AsyncSessionLocal
        from backend.app.models.agent_log import AgentLog
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(AgentLog).where(
                    AgentLog.workspace_id == workspace_id,
                    AgentLog.agent_id == agent_id,
                    AgentLog.level == "warning"
                )
            )
            logs = result.scalars().all()
            if any("Agent execution cancelled" in log.message for log in logs):
                print("  [PASS] Cancellation audit log FOUND! (Survived rollback)")
            else:
                print("  [FAIL] Cancellation audit log NOT FOUND!")

if __name__ == "__main__":
    asyncio.run(test_cancellation())
