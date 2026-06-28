import asyncio
import httpx
import uuid
import sys
import os

BASE_URL = "http://localhost:8000"

async def test_security():
    print("=================================================================")
    print("  VERIFICATION 5 & 6 – RATE LIMITING & IDEMPOTENCY / REPLAY")
    print("=================================================================")
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # Setup Isolated Tenant
        email = f"loadtest_sec_{uuid.uuid4().hex[:6]}@omniflow.ai"
        r_signup = await client.post("/api/v1/auth/signup", json={
            "email": email,
            "password": "securepassword123",
            "full_name": "Security Test User",
            "workspace_name": "LoadTest_Security"
        })
        
        data = r_signup.json().get("data", {})
        access_token = data.get("access_token")
        workspace_id = data.get("user", {}).get("workspace_id")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        print(f"\n[OK] Setup isolated tenant (Workspace: {workspace_id})")
        
        # Create an agent
        r_agent = await client.post(f"/api/v1/workspaces/{workspace_id}/agents", json={
            "name": "Sec Agent",
            "category": "test",
            "is_active": True
        }, headers=headers)
        agent_id = r_agent.json()["id"]
        
        # Set public allowed
        from sqlalchemy.sql import text
        from backend.app.core.database import engine
        async with engine.begin() as conn:
            await conn.execute(
                text("UPDATE agents SET is_public_allowed = true WHERE id = :id"),
                {"id": agent_id}
            )
            
        # Publish version
        r_ver = await client.post(f"/api/v1/workspaces/{workspace_id}/agents/{agent_id}/versions", json={
            "prompt": {"system_prompt": "You are a test agent.", "instructions": []},
            "model": {"provider": "gemini", "model_name": "gemini-2.5-flash", "config": {"temperature": 0.7}},
            "publish": True
        }, headers=headers)
        if r_ver.status_code >= 400:
            print("  [FAIL] Version publish:", r_ver.text)
        
        # API Key
        r_key = await client.post(f"/api/v1/api-keys", json={
            "name": "Test Key",
            "scopes": ["agent_chat"]
        }, headers=headers)
        api_key = r_key.json()["key_secret"]
        
        # ==========================================
        # VERIFICATION 6: IDEMPOTENCY (REPLAY)
        # ==========================================
        print("\n[IDEMPOTENCY / REPLAY TEST]")
        idempotency_key = f"idem_{uuid.uuid4().hex}"
        public_headers = {"X-Api-Key": api_key, "idempotency-key": idempotency_key}
        
        # Request 1
        r1 = await client.post(f"/api/public/v1/agents/{agent_id}/chat", headers=public_headers, json={"message": "Hello 1"})
        print(f"  [REQ 1] Status: {r1.status_code}")
        if r1.status_code >= 400:
            print(r1.text)
        assert r1.status_code == 200
        run_id_1 = r1.json()["data"]["run_id"]
        
        # Request 2 (Replay)
        r2 = await client.post(f"/api/public/v1/agents/{agent_id}/chat", headers=public_headers, json={"message": "Hello 2 - Different body but same key"})
        print(f"  [REQ 2] Status: {r2.status_code}")
        assert r2.status_code == 200
        run_id_2 = r2.json()["data"]["run_id"]
        
        if run_id_1 == run_id_2:
            print("  [OK] Idempotency successfully prevented second execution. Returned cached result.")
        else:
            print("  [FAIL] Idempotency failed. New run ID generated.")
            
        # Request 3 (Conflict - In Progress) -> Hard to simulate without race conditions, but we can verify completed state above.

        # ==========================================
        # VERIFICATION 5: RATE LIMITING
        # ==========================================
        print("\n[RATE LIMITING TEST]")
        # Public chat limit is 20 per minute. We already sent 2 (though the 2nd might bypass limit or count towards it depending on middleware order). 
        # We will blast 25 requests with DIFFERENT idempotency keys to ensure they all get processed until 429.
        
        rate_limit_hit = False
        success_count = 0
        for i in range(25):
            h = {"X-Api-Key": api_key, "idempotency-key": f"idem_burst_{i}"}
            
            # Or hit the public chat endpoint (but it will call Gemini 20 times)
            # We'll hit the Agent list endpoint which is 100/minute? Let's check public endpoint
            resp_pub = await client.post(f"/api/public/v1/agents/{agent_id}/chat", headers=h, json={"message": "hi"})
            if resp_pub.status_code == 429:
                rate_limit_hit = True
                print(f"  [OK] Rate limit exactly triggered at request {i+1} (Status 429).")
                break
            elif resp_pub.status_code == 200:
                success_count += 1
            else:
                print(f"  [WARN] Unexpected status {resp_pub.status_code}: {resp_pub.text}")
                
        if not rate_limit_hit:
            print(f"  [FAIL] Sent {success_count} requests and did not hit rate limit.")
            
        print("\n  RESULTS: Security checks completed.")

if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath("."))
    asyncio.run(test_security())
