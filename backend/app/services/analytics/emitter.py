"""
Phase 12: Analytics Event Emitter — Durable Outbox Pattern.

Writes analytics events into the `analytics_outbox` table inside the
SAME database transaction as the business action. This guarantees
no event loss during deployment, restart, crash, or worker termination.

The emitter never blocks or fails the caller. If the outbox write itself
fails (very unlikely since it's the same transaction), the error is
logged and swallowed so the business path is never impacted.

METADATA SANITIZATION
---------------------
Before persisting, the emitter scrubs metadata of sensitive fields
(raw customer text, PII) using a configurable whitelist.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.analytics import AnalyticsOutbox
from backend.app.schemas.analytics import AnalyticsEventType

logger = logging.getLogger(__name__)

# Fields that are safe to persist in analytics metadata.
_METADATA_WHITELIST = frozenset({
    "channel", "status", "priority", "stage", "issue_type",
    "complaint_type", "sentiment", "from_agent", "to_agent",
    "reason", "confidence", "latency_ms", "handoff_depth",
    "refund_requested", "refund_amount", "source_channel",
    "agent_name", "funnel_stage", "buying_intent", "lead_score",
    "event_subtype", "resolution_timeline", "schema_version",
})


def _sanitize_metadata(raw: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Strip non-whitelisted keys from metadata to prevent PII leakage."""
    if not raw:
        return raw
    return {k: v for k, v in raw.items() if k in _METADATA_WHITELIST}


class AnalyticsEventEmitter:
    """
    Durable outbox emitter. Call `emit()` inside any service method
    and the event will be written to the outbox in the same transaction.
    """

    @staticmethod
    async def emit(
        db: AsyncSession,
        workspace_id: UUID,
        event_type: AnalyticsEventType,
        conversation_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None,
        source_agent: Optional[str] = None,
        target_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        event_time: Optional[datetime] = None,
    ) -> None:
        """
        Write an outbox record inside the caller's transaction.

        Parameters
        ----------
        db : AsyncSession
            The session of the calling business transaction.
        event_time : datetime, optional
            The real time the event occurred. Defaults to now(UTC).
            Used for late-arrival / backfill scenarios.
        """
        try:
            # Validate event_type is a known enum member
            if isinstance(event_type, str):
                event_type = AnalyticsEventType(event_type)

            record = AnalyticsOutbox(
                id=uuid.uuid4(),
                workspace_id=workspace_id,
                conversation_id=conversation_id,
                customer_id=customer_id,
                event_type=event_type.value,
                source_agent=source_agent,
                target_agent=target_agent,
                event_metadata=_sanitize_metadata(metadata),
                idempotency_key=idempotency_key,
                schema_version=1,
                status="pending",
                attempts=0,
                created_at=event_time or datetime.now(timezone.utc),
            )
            db.add(record)
            # Do NOT commit — the caller's transaction will commit.
        except Exception as exc:
            # Never block the business path
            logger.error(
                "AnalyticsEventEmitter.emit failed (non-fatal): %s",
                exc.__class__.__name__,
                extra={
                    "event_type": event_type.value if isinstance(event_type, AnalyticsEventType) else str(event_type),
                    "workspace_id": str(workspace_id),
                    "conversation_id": str(conversation_id) if conversation_id else None,
                },
            )
