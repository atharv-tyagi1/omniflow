from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from uuid import UUID

from backend.app.core.database import get_db
from backend.app.services.telegram_service import TelegramService
from backend.app.core.response import success_response, error_response
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Receives incoming webhook updates from Telegram.
    Secures request via X-Telegram-Bot-Api-Secret-Token, validates idempotency
    of update_id, and enqueues to PublicAsyncJob for durable processing.
    """
    # 1. Authenticate webhook request
    secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    expected_secret = settings.TELEGRAM_WEBHOOK_SECRET
    if expected_secret:
        if not secret_header or secret_header != expected_secret:
            logger.warning("Rejecting unauthorized Telegram webhook request.")
            return JSONResponse(
                status_code=401,
                content=error_response(
                    code="UNAUTHORIZED",
                    message="Invalid or missing secret token header",
                    status_code=401,
                ),
            )

    try:
        update = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse Telegram webhook payload: {e}")
        return JSONResponse(
            status_code=400,
            content=error_response(code="BAD_REQUEST", message="Invalid JSON"),
        )

    # 2. Validate update structure
    update_id = update.get("update_id")
    if update_id is None:
        return JSONResponse(
            status_code=400,
            content=error_response(code="BAD_REQUEST", message="Missing update_id"),
        )

    message = update.get("message")
    if not message:
        return success_response(data={"status": "ignored - no message"})

    # 3. Resolve workspace context
    workspace_id_str = settings.DEFAULT_WORKSPACE_ID
    if not workspace_id_str:
        return JSONResponse(
            status_code=500,
            content=error_response(
                code="CONFIGURATION_ERROR",
                message="DEFAULT_WORKSPACE_ID is not configured",
                status_code=500,
            ),
        )
    try:
        workspace_id = UUID(workspace_id_str)
    except ValueError:
        return JSONResponse(
            status_code=500,
            content=error_response(
                code="CONFIGURATION_ERROR",
                message="DEFAULT_WORKSPACE_ID is not a valid UUID",
                status_code=500,
            ),
        )

    # 4. Enforce idempotency using update_id
    from backend.app.services.public.idempotency_service import IdempotencyService
    from backend.app.models.public_api import PublicAsyncJob
    from datetime import datetime, timezone, timedelta

    key = f"telegram_update_id:{update_id}"
    try:
        record, is_new = await IdempotencyService.get_or_create_idempotency_key(
            db, workspace_id, key, "/api/v1/telegram/webhook"
        )
    except Exception as e:
        logger.warning(f"Telegram webhook idempotency/concurrency check failed: {e}")
        return success_response(data={"status": "processing (duplicate or concurrent)"})

    if not is_new:
        return success_response(data={"status": "ignored - duplicate"})

    try:
        # 5. Enqueue update to durable job queue
        retention_days = getattr(settings, "ASYNC_JOB_RETENTION_DAYS", 30)
        expires_at = datetime.now(timezone.utc) + timedelta(days=retention_days)

        job = PublicAsyncJob(
            workspace_id=workspace_id,
            job_type="telegram_update",
            status="pending",
            expires_at=expires_at,
            result_payload=update,
        )
        db.add(job)
        await db.flush()

        # Complete idempotency key
        await IdempotencyService.complete_idempotency_request(
            db, record, {"status": "enqueued", "job_id": str(job.id)}
        )
        return success_response(data={"status": "enqueued", "job_id": str(job.id)})
    except Exception as e:
        await IdempotencyService.fail_idempotency_request(db, record)
        logger.error(f"Failed to enqueue Telegram update job: {e}")
        return JSONResponse(
            status_code=500,
            content=error_response(
                code="INTERNAL_SERVER_ERROR",
                message="Failed to process update",
                status_code=500,
            ),
        )


@router.post("/setup")
async def setup_telegram_webhook():
    """
    Utility endpoint to register the webhook URL with Telegram.
    Requires TELEGRAM_WEBHOOK_URL and TELEGRAM_BOT_TOKEN to be configured.
    """
    success = await TelegramService.setup_webhook()
    if success:
        return success_response(data={"message": "Webhook registered successfully"})
    return JSONResponse(
        status_code=400,
        content=error_response(
            code="WEBHOOK_SETUP_FAILED", message="Failed to register webhook", status_code=400
        ),
    )
