import uuid
from typing import Any
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.rate_limiter import rate_limit
from backend.app.core.webhook_auth import verify_webhook_signature
from backend.app.schemas.public_api import PublicResponse
from backend.app.models.public_api import PublicWebhook

router = APIRouter(prefix="/webhooks", tags=["public_webhooks"])

@router.post("/{source}", response_model=PublicResponse[dict[str, Any]])
async def receive_webhook(
    req: Request,
    source: str,
    webhook: PublicWebhook = Depends(verify_webhook_signature),
    db: AsyncSession = Depends(get_db),
    _=Depends(rate_limit(limit=100, window_seconds=60))
):
    """
    Receives verified webhooks. The verify_webhook_signature dependency
    checks HMAC, timestamps, replay protection, and source allowlisting.
    """
    # Simply log or process. In a real application, we'd route this 
    # to the appropriate internal processor based on the source.
    # For now we acknowledge the verified webhook.
    
    # Process payload if needed
    body = await req.json()
    
    return PublicResponse(success=True, data={"status": "received", "source": source})
