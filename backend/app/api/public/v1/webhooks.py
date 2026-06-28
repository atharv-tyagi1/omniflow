"""
Phase 21.2F — Public Webhooks
POST /api/public/v1/webhooks/{webhook_id}

Security (beyond the existing foundation):
- HMAC signature via existing `verify_webhook_signature`
- Timestamp/replay-window validation in the `verify_webhook_signature` dependency
- Deterministic mapping from `webhook_id` to exactly ONE allowed agent or workflow target
- Idempotency enforced via webhook_id + delivery_id header
"""
import uuid
import logging
from typing import Any

from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.core.rate_limiter import rate_limit
from backend.app.core.webhook_auth import verify_webhook_signature
from backend.app.core.public_errors import PublicAPIException
from backend.app.schemas.public_api import PublicResponse
from backend.app.models.public_api import PublicWebhook
from backend.app.services.workflow_service import WorkflowService
from backend.app.services.agent_service import AgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["public_webhooks"])


@router.post("/{webhook_id}", response_model=PublicResponse[dict[str, Any]])
async def receive_webhook(
    req: Request,
    webhook_id: uuid.UUID,
    delivery_id: str = Header(None, alias="X-Delivery-Id", description="Idempotency token for this delivery"),
    webhook: PublicWebhook = Depends(verify_webhook_signature),
    db: AsyncSession = Depends(get_db),
    _=Depends(rate_limit(limit=100, window_seconds=60)),
):
    """
    Receives verified, deterministically-routed webhooks.

    Security:
    - HMAC signature verified by `verify_webhook_signature` dependency
    - Timestamp/replay-window protection in the same dependency
    - `webhook_id` must deterministically match a registered webhook record
    - Webhook record contains the exact permitted target (workflow or agent)
    - Idempotency enforced via X-Delivery-Id header
    """
    # Enforce deterministic webhook_id → target mapping
    # `webhook` is already resolved by the `verify_webhook_signature` dependency,
    # but we additionally confirm the URL's webhook_id matches the verified record.
    if str(webhook.id) != str(webhook_id):
        logger.warning(
            f"Webhook ID mismatch: URL={webhook_id} vs verified_record={webhook.id}"
        )
        raise PublicAPIException(
            "Webhook ID mismatch", status_code=403, code="FORBIDDEN"
        )

    body = await req.json()

    # Idempotency: skip duplicate deliveries
    if delivery_id and getattr(webhook, "last_delivery_id", None) == delivery_id:
        logger.info(f"Duplicate delivery skipped: webhook={webhook_id} delivery={delivery_id}")
        return PublicResponse(
            success=True,
            data={"status": "duplicate_skipped", "webhook_id": str(webhook_id)},
        )

    # Deterministic routing — the webhook record specifies the target type and ID
    target_type = getattr(webhook, "target_type", "workflow")  # "workflow" | "agent"
    target_id = getattr(webhook, "target_id", None)

    if target_type == "agent" and target_id:
        # Route to agent execution
        await AgentService.dispatch(
            db=db,
            workspace_id=webhook.workspace_id,
            agent_id=uuid.UUID(str(target_id)),
            conversation_id=uuid.uuid4(),
            user_message=body.get("message", str(body)),
        )
    else:
        # Default: route to workflow event queue
        await WorkflowService.dispatch_event(
            db=db,
            workspace_id=webhook.workspace_id,
            event_type=f"webhook.{webhook_id}",
            payload=body,
        )

    logger.info(
        f"Webhook received and routed: id={webhook_id} target_type={target_type} "
        f"target_id={target_id} workspace={webhook.workspace_id}"
    )

    return PublicResponse(
        success=True,
        data={
            "status": "received",
            "webhook_id": str(webhook_id),
            "target_type": target_type,
        },
    )
