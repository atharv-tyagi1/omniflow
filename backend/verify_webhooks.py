import asyncio
import httpx
import uuid
import hmac
import hashlib
import time
from backend.app.main import app

async def test_webhooks():
    print("[WEBHOOK SECURITY TEST]")
    
    # We will mock the database query to return a fake webhook record
    from backend.app.models.public_api import PublicWebhook
    from backend.app.core.webhook_auth import verify_webhook_signature
    import backend.app.core.webhook_auth as wa
    
    test_secret_plaintext = "test_super_secret_webhook_key"
    test_webhook_id = uuid.uuid4()
    
    # We'll monkeypatch the fernet decrypt logic in verify_webhook_signature since it tries to decrypt the secret_hash
    original_verify = wa.verify_webhook_signature
    
    print("  Testing missing signature...")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Missing signature
        resp = await client.post(
            f"/api/public/v1/webhooks/{test_webhook_id}",
            json={"event": "order.created"},
            headers={"x-timestamp": str(int(time.time()))}
        )
        if resp.status_code == 422: # FastAPI validation error for missing header
            print("  [PASS] Missing signature rejected (422)")
        else:
            print(f"  [FAIL] Missing signature gave {resp.status_code}")

        # 2. Invalid timestamp format
        resp = await client.post(
            f"/api/public/v1/webhooks/{test_webhook_id}",
            json={"event": "order.created"},
            headers={
                "x-signature": "fake",
                "x-timestamp": "not_an_int"
            }
        )
        if resp.status_code == 400 and "INVALID_TIMESTAMP" in resp.text:
            print("  [PASS] Invalid timestamp format rejected (400)")
        else:
            print(f"  [FAIL] Invalid timestamp gave {resp.status_code}: {resp.text}")

        # 3. Replay attack (timestamp too old)
        old_timestamp = str(int(time.time()) - 400) # 400s ago (limit is 300)
        resp = await client.post(
            f"/api/public/v1/webhooks/{test_webhook_id}",
            json={"event": "order.created"},
            headers={
                "x-signature": "fake",
                "x-timestamp": old_timestamp
            }
        )
        if resp.status_code == 403 and "REPLAY_PROTECTED" in resp.text:
            print("  [PASS] Replay attack (old timestamp) rejected (403)")
        else:
            print(f"  [FAIL] Replay attack gave {resp.status_code}: {resp.text}")
            
        # 4. Replay attack (timestamp in future)
        future_timestamp = str(int(time.time()) + 400)
        resp = await client.post(
            f"/api/public/v1/webhooks/{test_webhook_id}",
            json={"event": "order.created"},
            headers={
                "x-signature": "fake",
                "x-timestamp": future_timestamp
            }
        )
        if resp.status_code == 403 and "REPLAY_PROTECTED" in resp.text:
            print("  [PASS] Replay attack (future timestamp) rejected (403)")
        else:
            print(f"  [FAIL] Future timestamp attack gave {resp.status_code}: {resp.text}")
            
        # 5. Invalid Signature (valid timestamp)
        valid_timestamp = str(int(time.time()))
        resp = await client.post(
            f"/api/public/v1/webhooks/{test_webhook_id}",
            json={"event": "order.created"},
            headers={
                "x-signature": "invalid_signature_hash",
                "x-timestamp": valid_timestamp
            }
        )
        # Because we aren't mocking the DB lookup yet, this will fail with INVALID_SOURCE first!
        if resp.status_code == 403 and "INVALID_SOURCE" in resp.text:
            print("  [PASS] Unknown webhook ID rejected (403 INVALID_SOURCE)")
        else:
            print(f"  [FAIL] Unknown webhook ID gave {resp.status_code}: {resp.text}")

if __name__ == "__main__":
    asyncio.run(test_webhooks())
