import pytest
from uuid import uuid4, UUID
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.config import settings
from backend.app.models.workspace import Workspace
from backend.app.models.customer import Customer
from backend.app.models.conversation import Conversation
from backend.app.models.public_api import PublicAsyncJob, IdempotencyKey
from backend.app.models.voice_interaction import VoiceInteraction
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.services.public.async_job_worker import PublicAsyncJobWorker
from backend.app.services.telegram_service import TelegramService


class MockGenaiClient:
    def __init__(self, api_key=None):
        self.models = MagicMock()
        self.models.generate_content = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is a transcribed voice message from Gemini."
        self.models.generate_content.return_value = mock_response


class MockGTTS:
    def __init__(self, text, lang):
        self.text = text
        self.lang = lang

    def write_to_fp(self, fp):
        fp.write(b"mock_ogg_audio_bytes")


@pytest.fixture(autouse=True)
def mock_agent_pipeline():
    from backend.app.schemas.ai import AIResponse
    from backend.app.schemas.router import IntentResult, AgentIntent

    # Mock IntentRouter.classify
    mock_classify = AsyncMock(
        return_value=IntentResult(primary_intent=AgentIntent.SUPPORT, confidence=0.9)
    )

    # Mock AIService.generate_response
    mock_generate = AsyncMock(
        return_value=AIResponse(
            content="Mock agent reply content",
            structured_data={
                "customer_reply": "Mock agent reply content",
                "issue_type": "setup",
                "probable_cause": "none",
                "troubleshooting_steps": [],
                "resolution_status": "open",
                "confidence": 0.9,
                "sources": [],
                "agent_name": "SupportAgent",
                "metadata": {},
                "handoff_recommended": False,
                "requires_human": False,
            },
            tokens_used=50,
        )
    )

    with patch(
        "backend.app.core.ai.intent_router.IntentRouter.classify", new=mock_classify
    ), patch(
        "backend.app.services.ai_service.AIService.generate_response",
        new=mock_generate,
    ):
        yield


@pytest.fixture
async def telegram_setup(db: AsyncSession):
    # Create a workspace
    ws = Workspace(id=uuid4(), name="Telegram Test Workspace", plan="pro")
    db.add(ws)
    await db.commit()
    await db.refresh(ws)
    ws_id = ws.id

    # Set DEFAULT_WORKSPACE_ID in settings
    orig_ws_id = settings.DEFAULT_WORKSPACE_ID
    settings.DEFAULT_WORKSPACE_ID = str(ws_id)

    # Configure bot token and webhook secret
    orig_bot_token = settings.TELEGRAM_BOT_TOKEN
    orig_webhook_url = settings.TELEGRAM_WEBHOOK_URL
    orig_webhook_secret = settings.TELEGRAM_WEBHOOK_SECRET

    settings.TELEGRAM_BOT_TOKEN = "dummy_bot_token"
    settings.TELEGRAM_WEBHOOK_URL = "https://example.com/webhook"
    settings.TELEGRAM_WEBHOOK_SECRET = "test_webhook_secret_123"

    yield ws_id

    # Restore settings
    settings.DEFAULT_WORKSPACE_ID = orig_ws_id
    settings.TELEGRAM_BOT_TOKEN = orig_bot_token
    settings.TELEGRAM_WEBHOOK_URL = orig_webhook_url
    settings.TELEGRAM_WEBHOOK_SECRET = orig_webhook_secret


@pytest.mark.asyncio
async def test_webhook_auth_failure(async_client: AsyncClient, telegram_setup):
    # Request without secret header
    resp = await async_client.post(
        "/api/v1/telegram/webhook",
        json={"update_id": 100, "message": {"text": "hello"}},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"

    # Request with invalid secret header
    resp = await async_client.post(
        "/api/v1/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong_secret"},
        json={"update_id": 100, "message": {"text": "hello"}},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_setup_webhook(async_client: AsyncClient, telegram_setup):
    with patch(
        "backend.app.services.telegram_service.httpx.AsyncClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.post = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True}
        mock_client.post.return_value = mock_resp
        mock_client_class.return_value.__aenter__.return_value = mock_client

        resp = await async_client.post("/api/v1/telegram/setup")
        assert resp.status_code == 200
        assert resp.json()["data"]["message"] == "Webhook registered successfully"

        # Check payload passed to setWebhook
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert kwargs["json"] == {
            "url": "https://example.com/webhook",
            "secret_token": "test_webhook_secret_123",
        }


@pytest.mark.asyncio
async def test_setup_webhook_failure(async_client: AsyncClient, telegram_setup):
    with patch(
        "backend.app.services.telegram_service.httpx.AsyncClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.post = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": False, "description": "invalid url"}
        mock_client.post.return_value = mock_resp
        mock_client_class.return_value.__aenter__.return_value = mock_client

        resp = await async_client.post("/api/v1/telegram/setup")
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "WEBHOOK_SETUP_FAILED"


@pytest.mark.asyncio
async def test_webhook_text_message_flow(
    async_client: AsyncClient, db: AsyncSession, telegram_setup
):
    headers = {"X-Telegram-Bot-Api-Secret-Token": "test_webhook_secret_123"}
    update_payload = {
        "update_id": 9999,
        "message": {
            "chat": {"id": 123456},
            "text": "Hello agent",
            "from": {"id": 789, "first_name": "Alice"},
        },
    }

    # 1. Enqueue job
    resp = await async_client.post(
        "/api/v1/telegram/webhook", headers=headers, json=update_payload
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "enqueued"
    job_id = resp.json()["data"]["job_id"]

    # Verify job was persisted in database as pending
    stmt = select(PublicAsyncJob).where(PublicAsyncJob.id == UUID(job_id))
    result = await db.execute(stmt)
    job = result.scalar_one()
    assert job.job_type == "telegram_update"
    assert job.status == "pending"
    assert job.result_payload["update_id"] == 9999

    # 2. Resend the same update (test idempotency)
    resp_dup = await async_client.post(
        "/api/v1/telegram/webhook", headers=headers, json=update_payload
    )
    assert resp_dup.status_code == 200
    assert resp_dup.json()["data"]["status"] == "ignored - duplicate"


@pytest.mark.asyncio
async def test_durable_processing_text(db: AsyncSession, telegram_setup):
    workspace_id = telegram_setup
    # Add a pending telegram update job directly
    job = PublicAsyncJob(
        workspace_id=workspace_id,
        job_type="telegram_update",
        status="pending",
        result_payload={
            "update_id": 10001,
            "message": {
                "chat": {"id": 123456},
                "text": "Hello there",
                "from": {"id": 789, "first_name": "Alice"},
            },
        },
    )
    db.add(job)
    await db.commit()
    job_id = job.id

    # Mock TelegramService.send_message
    with patch(
        "backend.app.services.telegram_service.TelegramService.send_message",
        new_callable=AsyncMock,
    ) as mock_send:
        mock_send.return_value = True

        # Run worker
        await PublicAsyncJobWorker.process_pending_jobs(db)

        # Refresh job
        stmt = select(PublicAsyncJob).where(PublicAsyncJob.id == job_id)
        res = await db.execute(stmt)
        refreshed_job = res.scalar_one()
        assert refreshed_job.status == "completed"

        # Verify customer was created
        stmt = select(Customer).where(Customer.telegram_id == "789")
        res = await db.execute(stmt)
        customer = res.scalar_one()
        assert customer.name == "Alice"
        assert customer.workspace_id == workspace_id

        # Verify conversation was created
        stmt = select(Conversation).where(Conversation.customer_id == customer.id)
        res = await db.execute(stmt)
        conversation = res.scalar_one()
        assert conversation.channel == "telegram_chat"


@pytest.mark.asyncio
async def test_durable_processing_voice(db: AsyncSession, telegram_setup):
    workspace_id = telegram_setup
    job = PublicAsyncJob(
        workspace_id=workspace_id,
        job_type="telegram_update",
        status="pending",
        result_payload={
            "update_id": 10002,
            "message": {
                "chat": {"id": 123456},
                "voice": {"file_id": "voice_file_abc", "duration": 5},
                "from": {"id": 789, "first_name": "Alice"},
            },
        },
    )
    db.add(job)
    await db.commit()
    job_id = job.id

    with patch(
        "backend.app.services.telegram_service.httpx.AsyncClient"
    ) as mock_client_class, patch(
        "google.genai.Client", new=MockGenaiClient
    ), patch(
        "gtts.gTTS", new=MockGTTS
    ):

        mock_client = MagicMock()
        mock_client.get = AsyncMock()
        mock_client.post = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock getFile response
        mock_get_file_resp = MagicMock()
        mock_get_file_resp.json.return_value = {
            "ok": True,
            "result": {"file_path": "voice/note.ogg"},
        }
        # Mock download response
        mock_download_resp = MagicMock()
        mock_download_resp.content = b"audio_bytes"

        def get_side_effect(url, *args, **kwargs):
            if "getFile" in str(url):
                return mock_get_file_resp
            else:
                return mock_download_resp

        mock_client.get.side_effect = get_side_effect

        # Mock sendVoice response
        mock_post_resp = MagicMock()
        mock_post_resp.json.return_value = {"ok": True}
        mock_client.post.return_value = mock_post_resp

        # Run worker
        await PublicAsyncJobWorker.process_pending_jobs(db)

        # Refresh job
        stmt = select(PublicAsyncJob).where(PublicAsyncJob.id == job_id)
        res = await db.execute(stmt)
        refreshed_job = res.scalar_one()
        assert refreshed_job.status == "completed"

        # Verify VoiceInteraction record was saved
        stmt = select(VoiceInteraction)
        res = await db.execute(stmt)
        voice_interaction = res.scalars().first()
        assert voice_interaction is not None
        assert voice_interaction.duration_seconds == 5
        assert "transcribed" in voice_interaction.transcript


@pytest.mark.asyncio
async def test_concurrent_customer_resolution(db: AsyncSession, telegram_setup):
    workspace_id = telegram_setup
    import asyncio

    # Run 10 concurrent creations
    tasks = [
        CustomerRepository.get_or_create_by_telegram_id(
            db=db,
            telegram_id="999",
            name=f"Concurrent-{i}",
            workspace_id=workspace_id,
        )
        for i in range(10)
    ]

    customers = await asyncio.gather(*tasks)

    # Verify all resolved to the exact same Customer ID
    first_id = customers[0].id
    for cust in customers:
        assert cust.id == first_id

    # Verify only one customer exists in DB
    stmt = select(Customer).where(Customer.telegram_id == "999")
    res = await db.execute(stmt)
    records = res.scalars().all()
    assert len(records) == 1


@pytest.mark.asyncio
async def test_unsupported_message_type(db: AsyncSession, telegram_setup):
    workspace_id = telegram_setup
    job = PublicAsyncJob(
        workspace_id=workspace_id,
        job_type="telegram_update",
        status="pending",
        result_payload={
            "update_id": 10003,
            "message": {
                "chat": {"id": 123456},
                "photo": [{"file_id": "photo_id"}],
                "from": {"id": 789, "first_name": "Alice"},
            },
        },
    )
    db.add(job)
    await db.commit()
    job_id = job.id

    # Run worker
    await PublicAsyncJobWorker.process_pending_jobs(db)

    # Job should be completed because unsupported types are skipped/ignored safely, not failing the job
    stmt = select(PublicAsyncJob).where(PublicAsyncJob.id == job_id)
    res = await db.execute(stmt)
    refreshed_job = res.scalar_one()
    assert refreshed_job.status == "completed"


@pytest.mark.asyncio
async def test_rollback_on_partial_failure(db: AsyncSession, telegram_setup):
    workspace_id = telegram_setup
    job = PublicAsyncJob(
        workspace_id=workspace_id,
        job_type="telegram_update",
        status="pending",
        max_attempts=1,
        result_payload={
            "update_id": 10004,
            "message": {
                "chat": {"id": 123456},
                "text": "Fail this",
                "from": {"id": 789, "first_name": "Alice"},
            },
        },
    )
    db.add(job)
    await db.commit()
    job_id = job.id

    with patch(
        "backend.app.services.conversation_service.ConversationService.add_message",
        side_effect=ValueError("Simulated Db Error"),
    ):
        # Run worker
        await PublicAsyncJobWorker.process_pending_jobs(db)

        # Refresh job
        stmt = select(PublicAsyncJob).where(PublicAsyncJob.id == job_id)
        res = await db.execute(stmt)
        refreshed_job = res.scalar_one()
        # It should have failed and last_error populated
        assert refreshed_job.status == "failed"
        assert "Simulated Db Error" in refreshed_job.last_error

        # Let's verify that no message was persisted (rollback checked)
        stmt = select(Customer).where(Customer.telegram_id == "789")
        res = await db.execute(stmt)
        customer = res.scalar_one_or_none()
        if customer:
            stmt = select(Conversation).where(
                Conversation.customer_id == customer.id
            )
            res = await db.execute(stmt)
            conversation = res.scalar_one_or_none()
            if conversation:
                from backend.app.models.message import Message

                stmt = select(Message).where(
                    Message.conversation_id == conversation.id
                )
                res = await db.execute(stmt)
                messages = res.scalars().all()
                assert not any(m.content == "Fail this" for m in messages)
