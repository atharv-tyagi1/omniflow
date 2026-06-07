import httpx
import asyncio

async def test_create_api_key():
    async with httpx.AsyncClient() as client:
        # 1. Sign up to get a real token
        signup_data = {
            "email": "test_apikey_creator@example.com",
            "password": "StrongPassword123!",
            "full_name": "API Key Tester",
            "company_name": "Test Corp"
        }
        res = await client.post("http://localhost:8000/api/v1/auth/signup", json=signup_data)
        if res.status_code not in (200, 201):
            # Maybe user exists, try login
            login_data = {
                "username": "test_apikey_creator@example.com",
                "password": "StrongPassword123!"
            }
            res = await client.post("http://localhost:8000/api/v1/auth/login", data=login_data)
        
        if res.status_code != 200:
            print("Auth failed:", res.status_code, res.text)
            return
            
        token = res.json().get("access_token")
        print("Got token.")
        
        # 2. Try to create API Key
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "name": "Test Key",
            "scopes": ["all"]
        }
        
        print(f"Request: POST /api/v1/api-keys")
        print(f"Headers: {headers}")
        print(f"Body: {payload}")
        
        create_res = await client.post("http://localhost:8000/api/v1/api-keys", headers=headers, json=payload)
        
        print("\nResponse:")
        print(f"Status: {create_res.status_code}")
        print(f"Body: {create_res.text}")

if __name__ == "__main__":
    asyncio.run(test_create_api_key())
