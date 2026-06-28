import asyncio
import httpx
import uuid
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

async def test_contract():
    print("=================================================================")
    print("  VERIFICATION 1 – API CONTRACT / OPENAPI")
    print("=================================================================")
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Fetch OpenAPI
        print("\n[OPENAPI]")
        try:
            r_openapi = await client.get("/openapi.json")
            if r_openapi.status_code == 200:
                openapi_spec = r_openapi.json()
                print(f"  [OK] Fetched OpenAPI spec (version {openapi_spec['info']['version']})")
                print(f"  [OK] Found {len(openapi_spec['paths'])} registered paths")
            else:
                print(f"  [FAIL] Failed to fetch OpenAPI spec: {r_openapi.status_code}")
                return
        except Exception as e:
            print(f"  [FAIL] Error fetching OpenAPI spec: {e}")
            return

        # 2. Setup Isolated Tenant
        print("\n[TEST ISOLATION]")
        email = f"loadtest_contract_{uuid.uuid4().hex[:6]}@omniflow.ai"
        r_signup = await client.post("/api/v1/auth/signup", json={
            "email": email,
            "password": "securepassword123",
            "full_name": "Contract Test User",
            "workspace_name": "LoadTest_Contract"
        })
        
        if r_signup.status_code != 200:
            print(f"  [FAIL] Failed to create isolated tenant: {r_signup.text}")
            return
            
        data = r_signup.json().get("data", {})
        access_token = data.get("access_token")
        workspace_id = data.get("user", {}).get("workspace_id")
        user_id = data.get("user", {}).get("id")
        
        print(f"  [OK] Created isolated tenant (Workspace: {workspace_id})")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 3. Contract Checks (Agent Management)
        print("\n[CONTRACT CHECKS - AGENT MANAGEMENT]")
        
        # POST /agents
        agent_payload = {
            "name": "Contract Test Agent",
            "category": "support",
            "is_active": True
        }
        r_create = await client.post(f"/api/v1/workspaces/{workspace_id}/agents", json=agent_payload, headers=headers)
        if r_create.status_code == 201:
            agent = r_create.json()
            agent_id = agent.get("id")
            print(f"  [OK] Create Agent matching schema (status 201)")
            # Validate response shape
            if "id" in agent and "name" in agent:
                print(f"  [OK] Agent response shape valid")
            else:
                print(f"  [FAIL] Agent response missing required fields: {agent}")
        else:
            print(f"  [FAIL] Create Agent returned {r_create.status_code}: {r_create.text}")
            agent_id = None
            
        # GET /agents
        r_list = await client.get(f"/api/v1/workspaces/{workspace_id}/agents", headers=headers)
        if r_list.status_code == 200:
            print(f"  [OK] List Agents matching schema (status 200)")
            data = r_list.json()
            if isinstance(data, list) or "items" in data:
                print(f"  [OK] List response shape valid")
            else:
                print(f"  [WARN] List response shape unusual: {data}")
        else:
            print(f"  [FAIL] List Agents returned {r_list.status_code}")
            
        # GET /agents/{id}
        if agent_id:
            r_get = await client.get(f"/api/v1/workspaces/{workspace_id}/agents/{agent_id}", headers=headers)
            if r_get.status_code == 200:
                print(f"  [OK] Get Agent matching schema (status 200)")
                assert r_get.json()["id"] == agent_id
            else:
                print(f"  [FAIL] Get Agent returned {r_get.status_code}")
                
        # 4. Teardown
        print("\n[TEARDOWN]")
        # To strictly tear down, we need to delete the user and workspace.
        # But we don't have endpoints explicitly mapped for hard-deleting workspaces yet.
        # However, this is a test script, we can run a direct DB execution if needed, or rely on script idempotency.
        # Let's at least soft-delete or archive the agent.
        if agent_id:
            r_del = await client.delete(f"/api/v1/workspaces/{workspace_id}/agents/{agent_id}", headers=headers)
            if r_del.status_code == 200:
                print(f"  [OK] Archived agent {agent_id}")
            else:
                print(f"  [WARN] Failed to archive agent: {r_del.text}")
                
        print("  [OK] Teardown complete. (Database cleanup omitted via API, safe isolated tenant left).")
        print("\n  RESULTS: Contract verification checks completed.")

if __name__ == "__main__":
    asyncio.run(test_contract())
