import pytest
import uuid
from typing import AsyncGenerator
import time
import hmac
import hashlib

from backend.app.models.public_api import PublicApiKey, PublicApiKeyScope, PublicApiKeyRotation, IdempotencyKey, PublicWebhook, PublicAsyncJob
from backend.app.services.public.public_api_service import PublicApiService

@pytest.fixture
def db_session(db):
    return db

@pytest.fixture
async def workspace(db):
    from backend.app.models.workspace import Workspace
    workspace = Workspace(id=uuid.uuid4(), name="Test Workspace", plan="pro")
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)
    return workspace

@pytest.fixture
async def user(db, workspace):
    from backend.app.models.user import User
    from backend.app.models.workspace_member import WorkspaceMember
    user = User(
        id=uuid.uuid4(),
        email=f"user_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Test User",
        password_hash="dummy_hash",
        status="active"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role="owner"
    )
    db.add(member)
    await db.commit()
    return user

@pytest.fixture
async def public_api_key_data(db_session, workspace, user) -> dict:
    plain_key = await PublicApiService.create_api_key(
        db_session, workspace.id, user.id, "Test Key", ["chat", "analytics_read", "intel_read"]
    )
    return {"key": plain_key, "workspace_id": workspace.id}

@pytest.mark.asyncio
async def test_api_key_auth_and_scopes(async_client, public_api_key_data):
    # Test valid key + scope
    headers = {"X-Api-Key": public_api_key_data["key"]}
    response = await async_client.get("/api/public/v1/analytics/overview", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Test invalid key
    headers_invalid = {"X-Api-Key": "invalid_key_1234"}
    response = await async_client.get("/api/public/v1/analytics/overview", headers=headers_invalid)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"

@pytest.mark.asyncio
async def test_rotation_audit_trail(db_session, public_api_key_data, user):
    from sqlalchemy import select
    # Get the key record
    stmt = select(PublicApiKey).where(PublicApiKey.workspace_id == public_api_key_data["workspace_id"])
    result = await db_session.execute(stmt)
    key_record = result.scalars().first()
    assert key_record is not None

    old_prefix = key_record.prefix
    
    # Rotate
    new_plain_key = await PublicApiService.rotate_api_key(
        db_session, public_api_key_data["workspace_id"], key_record.id, user.id
    )

    await db_session.refresh(key_record)
    assert key_record.status == "revoked"
    
    # Check audit trail
    stmt = select(PublicApiKeyRotation).where(PublicApiKeyRotation.api_key_id == key_record.id)
    result = await db_session.execute(stmt)
    audit = result.scalars().first()
    assert audit is not None
    assert audit.old_key_prefix == old_prefix
    assert audit.new_key_prefix == key_record.prefix

@pytest.mark.asyncio
async def test_webhook_signature_verification(async_client, db_session, workspace):
    import base64
    from cryptography.fernet import Fernet
    from backend.app.core.config import settings

    derived_key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    fernet = Fernet(base64.urlsafe_b64encode(derived_key))
    encrypted_secret = fernet.encrypt("my_secret".encode()).decode()

    webhook = PublicWebhook(
        workspace_id=workspace.id,
        source="shopify",
        secret_hash=encrypted_secret,
        is_active=True
    )
    db_session.add(webhook)
    await db_session.commit()

    timestamp = str(int(time.time()))
    payload = b'{"event":"order.created"}'
    payload_to_sign = f"{timestamp}.".encode() + payload
    
    valid_signature = hmac.new("my_secret".encode(), payload_to_sign, hashlib.sha256).hexdigest()

    headers = {
        "X-Signature": valid_signature,
        "X-Timestamp": timestamp,
        "Content-Type": "application/json"
    }

    resp = await async_client.post("/api/public/v1/webhooks/shopify", content=payload, headers=headers)
    assert resp.status_code == 200

    # Test invalid signature
    headers["X-Signature"] = "invalid"
    resp = await async_client.post("/api/public/v1/webhooks/shopify", content=payload, headers=headers)
    assert resp.status_code == 403

    # Test replay protection
    headers["X-Signature"] = valid_signature
    headers["X-Timestamp"] = str(int(time.time()) - 1000) # expired
    resp = await async_client.post("/api/public/v1/webhooks/shopify", content=payload, headers=headers)
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_async_chat_behavior(async_client, public_api_key_data):
    headers = {
        "X-Api-Key": public_api_key_data["key"],
        "Idempotency-Key": str(uuid.uuid4())
    }
    payload = {
        "external_customer_id": "cust_123",
        "customer_name": "Test User",
        "message": "Hello async",
        "response_mode": "async"
    }
    
    resp = await async_client.post("/api/public/v1/chat", json=payload, headers=headers)
    assert resp.status_code == 202
    data = resp.json()["data"]
    assert "job_id" in data
    assert "status_url" in data

    # Check status endpoint
    status_resp = await async_client.get(data["status_url"], headers=headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["data"]["status"] == "pending"

@pytest.mark.asyncio
async def test_idempotency_expiration(db_session, workspace):
    from backend.app.services.public.idempotency_service import IdempotencyService
    import datetime
    
    # Create an expired record
    expired = IdempotencyKey(
        workspace_id=workspace.id,
        idempotency_key="expired_123",
        path="/test",
        status="completed",
        expires_at=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    )
    db_session.add(expired)
    await db_session.commit()

    await IdempotencyService.cleanup_expired_keys(db_session)
    
    from sqlalchemy import select
    stmt = select(IdempotencyKey).where(IdempotencyKey.idempotency_key == "expired_123")
    res = await db_session.execute(stmt)
    assert res.scalar_one_or_none() is None

@pytest.mark.asyncio
async def test_public_error_envelope(async_client, public_api_key_data):
    headers = {"X-Api-Key": public_api_key_data["key"]}
    # Force a validation error (missing required field)
    payload = {
        "customer_name": "Test User"
        # missing external_customer_id, message
    }
    resp = await async_client.post("/api/public/v1/chat", json=payload, headers=headers)
    assert resp.status_code == 422
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in data["metadata"]
