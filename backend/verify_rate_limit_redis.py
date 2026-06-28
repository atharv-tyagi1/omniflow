import asyncio
import os
import sys
import httpx
import logging
logging.basicConfig(level=logging.INFO)
import uuid

os.environ["ENVIRONMENT"] = "production"
os.environ["REDIS_URL"] = "fakeredis"

sys.path.insert(0, os.path.abspath("."))
import asyncio
from backend.app.main import app
from backend.app.core.config import settings

settings.ENVIRONMENT = "production"
settings.REDIS_URL = "fakeredis"

async def test_rate_limit():
    
    import backend.app.core.rate_limiter
    backend.app.core.rate_limiter.get_redis_client()
    
    import backend.app.core.public_auth as pa
    async def mock_verify(*args, **kwargs):
        return True
    pa.verify_api_key_hash = mock_verify

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Setup isolated tenant via APIs
        print("  Creating tenant...")
        r_signup = await client.post("/api/v1/auth/signup", json={
            "email": f"test_{uuid.uuid4().hex}@test.com",
            "password": "password123",
            "full_name": "Test User",
            "workspace_name": "Test Workspace",
            "company_name": "Test Co"
        })
        if r_signup.status_code >= 400:
            print(f"Signup failed: {r_signup.text}")
            return
        token = r_signup.json()["data"]["access_token"]
        workspace_id = r_signup.json()["data"]["user"]["workspace_id"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("  Creating agent...")
        r_agent = await client.post(f"/api/v1/workspaces/{workspace_id}/agents", json={
            "name": "Test Agent",
            "category": "test",
            "description": "Test"
        }, headers=headers)
        if r_agent.status_code >= 400:
            print(f"Agent creation failed: {r_agent.text}")
            return
        
        agent_json = r_agent.json()
        print("Agent json:", agent_json)
        agent_id = agent_json["data"]["id"] if "data" in agent_json else agent_json["id"]
        
        # Publish version so public chat works
        await client.post(f"/api/v1/workspaces/{workspace_id}/agents/{agent_id}/versions", json={
            "prompt": {"system_prompt": "You are a test agent.", "instructions": []},
            "model": {"provider": "gemini", "model_name": "gemini-2.5-flash", "config": {"temperature": 0.7}},
            "publish": True
        }, headers=headers)

        # Allow public via DB query (API doesn't expose it yet)
        from backend.app.core.database import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as db:
            await db.execute(text("UPDATE agents SET is_public_allowed = true WHERE id = :id"), {"id": agent_id})
            await db.commit()

        print("  Creating API Key...")
        r_key = await client.post(f"/api/v1/api-keys", json={
            "name": "Rate Limit Test Key",
            "scopes": ["agent_chat"]
        }, headers=headers)
        
        if r_key.status_code != 200:
            print("Failed to create API key:", r_key.text)
            return
            
        key_json = r_key.json()
        print("Key json:", key_json)
        api_key = key_json["data"]["key_secret"] if "data" in key_json else key_json["key_secret"]

        print("\n[REDIS RATE LIMITING TEST]")
        print("  Mocking LLM to return instantly...")
        from backend.app.services.agent_service import AgentService
        
        async def mock_dispatch(*args, **kwargs):
            return {"content": "mocked", "status": "success", "run_id": str(uuid.uuid4())}
            
        AgentService.dispatch = mock_dispatch

        print("  Sending 25 sequential requests to trigger 20 req/min limit...")
        
        h = {"X-Api-Key": api_key}
        responses = []
        for i in range(25):
            req_headers = {**h, "idempotency-key": f"idem_redis_{i}"}
            resp = await client.post(
                f"/api/public/v1/agents/{agent_id}/chat",
                headers=req_headers,
                json={"message": "hello", "stream": False}
            )
            responses.append(resp)
            
        status_codes = [r.status_code for r in responses]
        
        
        
        print(f"  Status codes received: {status_codes}")
        
        count_200 = status_codes.count(200)
        count_429 = status_codes.count(429)
        
        print(f"  Successful requests (200): {count_200}")
        print(f"  Rate limited requests (429): {count_429}")
        
        if count_429 >= 5:
            print("  [OK] Rate limit successfully enforced via Redis implementation!")
        else:
            print("  [FAIL] Did not get expected 429s.")
            exit(1)

if __name__ == "__main__":
    asyncio.run(test_rate_limit())
