from fastapi import APIRouter, Depends, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from backend.app.core.database import get_db
from backend.app.services.telegram_service import TelegramService
from backend.app.core.response import success_response, error_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Receives incoming webhook updates from Telegram.
    Processes the message asynchronously so Telegram gets a fast 200 OK.
    """
    try:
        update = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse Telegram webhook payload: {e}")
        return error_response(code="BAD_REQUEST", message="Invalid JSON")

    message = update.get("message")
    if not message:
        return success_response(data={"status": "ignored - no message"})

    # Determine message type
    if "text" in message:
        # Route to text handler
        background_tasks.add_task(TelegramService.handle_text_message, db, message)
    elif "voice" in message:
        # Route to voice handler
        background_tasks.add_task(TelegramService.handle_voice_message, db, message)
    else:
        logger.info("Ignored unsupported message type from Telegram.")

    # Always return 200 OK immediately so Telegram doesn't retry
    return success_response(data={"status": "processing"})


@router.post("/setup")
async def setup_telegram_webhook():
    """
    Utility endpoint to register the webhook URL with Telegram.
    Requires TELEGRAM_WEBHOOK_URL and TELEGRAM_BOT_TOKEN to be configured.
    """
    success = await TelegramService.setup_webhook()
    if success:
        return success_response(message="Webhook registered successfully")
    return error_response(
        code="WEBHOOK_SETUP_FAILED", message="Failed to register webhook"
    )
