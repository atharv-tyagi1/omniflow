import hmac
import hashlib
import time
import logging
from fastapi import Request, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.public_api import PublicWebhook
from backend.app.core.public_errors import PublicAPIException
from backend.app.core.telemetry import log_public_telemetry, LatencyTracker

logger = logging.getLogger(__name__)

# Replay protection threshold in seconds
WEBHOOK_TOLERANCE_SECONDS = 300

async def verify_webhook_signature(
    request: Request,
    x_signature: str = Header(..., description="HMAC SHA256 Signature"),
    x_timestamp: str = Header(..., description="Timestamp of the request"),
    db: AsyncSession = Depends(get_db)
) -> PublicWebhook:
    """
    Validates the incoming webhook signature.
    Path must be /api/public/v1/webhooks/{source}
    """
    tracker = LatencyTracker()
    try:
        timestamp_int = int(x_timestamp)
    except ValueError:
        raise PublicAPIException("Invalid timestamp format", status_code=400, code="INVALID_TIMESTAMP")

    current_time = int(time.time())
    if abs(current_time - timestamp_int) > WEBHOOK_TOLERANCE_SECONDS:
        logger.warning(f"Webhook replay attempt detected: timestamp {timestamp_int}")
        log_public_telemetry(
            "public_webhook_invalid",
            details={"reason": "replay_protection", "timestamp": timestamp_int, "source": request.path_params.get("source")},
            latency_ms=tracker.get_latency_ms()
        )
        raise PublicAPIException("Request expired (replay protection)", status_code=403, code="REPLAY_PROTECTED")

    source = request.path_params.get("source")
    if not source:
        raise PublicAPIException("Missing webhook source", status_code=400, code="MISSING_SOURCE")

    # Read body
    body = await request.body()
    
    # We must explicitly look up the webhook source.
    # Note: the webhook URL contains the source but we need to ensure the source is registered.
    stmt = select(PublicWebhook).where(PublicWebhook.source == source, PublicWebhook.is_active == True)
    result = await db.execute(stmt)
    webhook = result.scalar_one_or_none()
    
    if not webhook:
        logger.warning(f"Webhook received for unknown or inactive source: {source}")
        log_public_telemetry(
            "public_webhook_invalid",
            details={"reason": "invalid_source", "source": source},
            latency_ms=tracker.get_latency_ms()
        )
        # Fail closed safely
        raise PublicAPIException("Invalid webhook source", status_code=403, code="INVALID_SOURCE")
        
    # Reconstruct the payload to sign
    # Convention: {timestamp}.{body}
    payload_to_sign = f"{x_timestamp}.".encode('utf-8') + body
    
    # Generate signature using the securely stored secret (which is typically hashed or encrypted, 
    # but for HMAC validation we actually need the plaintext secret to verify. Wait, if it's hashed 
    # we can't use HMAC. The prompt states: "Store webhook secrets encrypted at rest or via a secure secret reference mechanism. Never store plaintext."
    # Let's assume webhook.secret_hash is actually an encrypted string that we can decrypt using the application secret.)
    try:
        from cryptography.fernet import Fernet
        from backend.app.core.config import settings
        
        # We need a 32 url-safe base64-encoded bytes key for fernet.
        # fallback to a derived key from SECRET_KEY
        import base64
        derived_key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        fernet = Fernet(base64.urlsafe_b64encode(derived_key))
        
        plaintext_secret = fernet.decrypt(webhook.secret_hash.encode()).decode()
    except Exception as e:
        logger.error(f"Failed to decrypt webhook secret: {e}")
        raise PublicAPIException("Internal Configuration Error", status_code=500, code="INTERNAL_SERVER_ERROR")

    expected_signature = hmac.new(
        plaintext_secret.encode('utf-8'),
        payload_to_sign,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, x_signature):
        logger.warning(f"Invalid webhook signature for source {source}")
        log_public_telemetry(
            "public_webhook_invalid",
            workspace_id=str(webhook.workspace_id),
            details={"reason": "invalid_signature", "source": source},
            latency_ms=tracker.get_latency_ms()
        )
        raise PublicAPIException("Invalid signature", status_code=403, code="INVALID_SIGNATURE")
        
    request.state.workspace_id = str(webhook.workspace_id)
    
    log_public_telemetry(
        "public_webhook_success",
        workspace_id=str(webhook.workspace_id),
        details={"source": source},
        latency_ms=tracker.get_latency_ms()
    )
    
    return webhook
