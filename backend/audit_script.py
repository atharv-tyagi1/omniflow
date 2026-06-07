import httpx
import uuid

async def run_audit():
    async with httpx.AsyncClient() as client:
        # 1. Signup a test user
        email = f"audit_{uuid.uuid4().hex[:8]}@example.com"
        res = await client.post("http://localhost:8000/api/v1/auth/signup", json={
            "email": email,
            "password": "Password123!",
            "full_name": "Audit User",
            "workspace_name": "Audit Workspace"
        })
        print(f"Signup: {res.status_code}")
        if res.status_code != 200:
            print(res.text)
            return
            
        token = res.json()["data"]["access_token"]
        
        # 2. EXACT FRONTEND REQUEST
        print("\n--- FRONTEND REQUEST ---")
        print("POST /api/v1/api-keys")
        print(f"Headers: Authorization: Bearer {token[:10]}...")
        payload = {"name": "Test Key", "scopes": ["all"]}
        print(f"Body: {payload}")
        
        # 3. Perform Create API Key
        res_create = await client.post(
            "http://localhost:8000/api/v1/api-keys",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 4. CAPTURE BACKEND RESPONSE
        print("\n--- BACKEND RESPONSE ---")
        print(f"Status Code: {res_create.status_code}")
        print(f"Response Body: {res_create.text}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_audit())
