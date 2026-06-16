import pytest
from httpx import AsyncClient
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.public.public_api_service import PublicApiService

@pytest.fixture
async def workspace(db):
    from backend.app.models.workspace import Workspace
    workspace = Workspace(id=uuid.uuid4(), name="Test Workspace Voice", plan="pro")
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
async def public_api_key_data(db: AsyncSession, workspace, user) -> dict:
    plain_key = await PublicApiService.create_api_key(
        db, workspace.id, user.id, "Test Key", ["chat", "analytics_read", "intel_read"]
    )
    return {"key": plain_key, "workspace_id": workspace.id}

@pytest.mark.asyncio
async def test_voice_endpoint_rejects_large_files(async_client: AsyncClient, public_api_key_data: dict):
    # Create a dummy payload > 10MB
    large_payload = b"0" * (11 * 1024 * 1024)
    
    response = await async_client.post(
        "/api/public/v1/voice",
        headers={
            "X-Api-Key": public_api_key_data["key"],
            "Idempotency-Key": str(uuid.uuid4())
        },
        data={
            "external_customer_id": "cust_123",
            "customer_name": "John Doe",
        },
        files={
            "audio": ("test.wav", large_payload, "audio/wav")
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "too large" in data["error"].get("message", data["error"].get("details", "")).lower()

@pytest.mark.asyncio
async def test_voice_endpoint_rejects_unsupported_mime(async_client: AsyncClient, public_api_key_data: dict):
    response = await async_client.post(
        "/api/public/v1/voice",
        headers={
            "X-Api-Key": public_api_key_data["key"],
            "Idempotency-Key": str(uuid.uuid4())
        },
        data={
            "external_customer_id": "cust_123",
            "customer_name": "John Doe",
        },
        files={
            "audio": ("test.txt", b"hello", "text/plain")
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "unsupported audio format" in data["error"].get("message", data["error"].get("details", "")).lower()

@pytest.mark.asyncio
async def test_voice_endpoint_missing_headers(async_client: AsyncClient, public_api_key_data: dict):
    response = await async_client.post(
        "/api/public/v1/voice",
        headers={
            "X-Api-Key": public_api_key_data["key"],
            # Missing Idempotency-Key
        },
        data={
            "external_customer_id": "cust_123",
            "customer_name": "John Doe",
        },
        files={
            "audio": ("test.wav", b"fake audio", "audio/wav")
        }
    )
    
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_voice_endpoint_idempotency(async_client: AsyncClient, public_api_key_data: dict, db: AsyncSession):
    idempotency_key = str(uuid.uuid4())
    
    # Send first request (async mode for speed, avoiding real Gemini/GTTS)
    response1 = await async_client.post(
        "/api/public/v1/voice",
        headers={
            "X-Api-Key": public_api_key_data["key"],
            "Idempotency-Key": idempotency_key
        },
        data={
            "external_customer_id": "cust_123",
            "customer_name": "John Doe",
            "async_mode": "true"
        },
        files={
            "audio": ("test.wav", b"dummy_audio", "audio/wav")
        }
    )
    
    assert response1.status_code == 202
    
    # Send second request with same idempotency key
    response2 = await async_client.post(
        "/api/public/v1/voice",
        headers={
            "X-Api-Key": public_api_key_data["key"],
            "Idempotency-Key": idempotency_key
        },
        data={
            "external_customer_id": "cust_123",
            "customer_name": "John Doe",
            "async_mode": "true"
        },
        files={
            "audio": ("test.wav", b"dummy_audio", "audio/wav")
        }
    )
    
    # It should not fail with 409, it should either return 200 or 202 depending on the router implementation
    assert response2.status_code in (200, 202)
