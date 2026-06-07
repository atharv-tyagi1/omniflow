"""
Phase 12: Historical Backfill Job.

Idempotent, resumable, safe on large datasets.
Seeds analytics_events from existing Conversation, Handoff, Ticket, and
CustomerCareCase records, then rebuilds rollups.

Rerunning produces identical results (no duplicate events, correct rollups).
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.conversation import Conversation
from backend.app.models.handoff import Handoff
from backend.app.models.ticket import Ticket
from backend.app.models.customer_care_case import CustomerCareCase
from backend.app.models.analytics import AnalyticsEvent
from backend.app.schemas.analytics import AnalyticsEventType
from backend.app.services.analytics.worker import AnalyticsWorker

logger = logging.getLogger(__name__)


class AnalyticsBackfill:
    """
    Historical backfill from existing domain tables.
    Each record is assigned a deterministic idempotency_key so re-runs
    never create duplicates.
    """

    @staticmethod
    async def run(db: AsyncSession, workspace_id: UUID | None = None) -> dict:
        """
        Run the full backfill. Returns counts of inserted events.

        Parameters
        ----------
        workspace_id : optional
            If provided, backfill only that workspace. Otherwise backfill all.
        """
        import time
        start_time = time.time()
        
        counts = {
            "conversations": 0,
            "handoffs": 0,
            "tickets": 0,
            "customer_care": 0,
        }
        
        failed = 0

        try:
            counts["conversations"] = await AnalyticsBackfill._backfill_conversations(db, workspace_id)
            counts["handoffs"] = await AnalyticsBackfill._backfill_handoffs(db, workspace_id)
            counts["tickets"] = await AnalyticsBackfill._backfill_tickets(db, workspace_id)
            counts["customer_care"] = await AnalyticsBackfill._backfill_customer_care(db, workspace_id)

            await db.commit()

            # Rebuild rollups from the newly inserted events
            total_events = await AnalyticsWorker.rebuild_rollups(db, workspace_id=workspace_id)
            logger.info("Backfill complete: %s events -> %d rollup events processed", counts, total_events)
        except Exception as exc:
            failed = 1
            logger.error("Backfill failed: %s", exc, exc_info=True)
            raise
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(
                "Operational Metric: Backfill Completed",
                extra={
                    "metric_name": "backfill_duration_ms",
                    "duration_ms": duration_ms,
                    "backfill_failures": failed,
                    "workspace_id": str(workspace_id) if workspace_id else None
                }
            )

        return counts

    @staticmethod
    async def _backfill_conversations(db: AsyncSession, workspace_id: UUID | None) -> int:
        filters = []
        if workspace_id:
            filters.append(Conversation.workspace_id == workspace_id)

        stmt = select(Conversation).where(*filters)
        result = await db.execute(stmt)
        conversations = result.scalars().all()

        inserted = 0
        for conv in conversations:
            key = f"backfill:conversation_started:{conv.id}"
            if await AnalyticsBackfill._exists(db, key):
                continue

            event = AnalyticsEvent(
                workspace_id=conv.workspace_id,
                conversation_id=conv.id,
                customer_id=conv.customer_id,
                event_type=AnalyticsEventType.CONVERSATION_STARTED.value,
                event_metadata={"channel": conv.channel, "status": conv.status},
                idempotency_key=key,
                schema_version=1,
                created_at=conv.started_at or conv.created_at if hasattr(conv, 'created_at') else datetime.now(timezone.utc),
            )
            db.add(event)
            inserted += 1

            # If conversation is completed/resolved/closed, add completion event
            if conv.status in ("resolved", "closed", "completed"):
                comp_key = f"backfill:conversation_completed:{conv.id}"
                if not await AnalyticsBackfill._exists(db, comp_key):
                    comp_event = AnalyticsEvent(
                        workspace_id=conv.workspace_id,
                        conversation_id=conv.id,
                        customer_id=conv.customer_id,
                        event_type=AnalyticsEventType.CONVERSATION_COMPLETED.value,
                        idempotency_key=comp_key,
                        schema_version=1,
                        created_at=conv.ended_at or datetime.now(timezone.utc),
                    )
                    db.add(comp_event)
                    inserted += 1

        return inserted

    @staticmethod
    async def _backfill_handoffs(db: AsyncSession, workspace_id: UUID | None) -> int:
        filters = []
        if workspace_id:
            filters.append(Handoff.workspace_id == workspace_id)

        stmt = select(Handoff).where(*filters)
        result = await db.execute(stmt)
        handoffs = result.scalars().all()

        inserted = 0
        for h in handoffs:
            if h.status == "completed":
                event_type = AnalyticsEventType.HANDOFF_COMPLETED
            elif h.status == "failed":
                event_type = AnalyticsEventType.HANDOFF_FAILED
            else:
                event_type = AnalyticsEventType.HANDOFF_CREATED

            key = f"backfill:{event_type.value}:{h.id}"
            if await AnalyticsBackfill._exists(db, key):
                continue

            event = AnalyticsEvent(
                workspace_id=h.workspace_id,
                conversation_id=h.conversation_id,
                event_type=event_type.value,
                source_agent=h.from_agent,
                target_agent=h.to_agent,
                event_metadata={"reason": h.reason, "confidence": h.confidence, "status": h.status},
                idempotency_key=key,
                schema_version=1,
                created_at=h.created_at,
            )
            db.add(event)
            inserted += 1

        return inserted

    @staticmethod
    async def _backfill_tickets(db: AsyncSession, workspace_id: UUID | None) -> int:
        filters = []
        if workspace_id:
            filters.append(Ticket.workspace_id == workspace_id)

        stmt = select(Ticket).where(*filters)
        result = await db.execute(stmt)
        tickets = result.scalars().all()

        inserted = 0
        for t in tickets:
            create_key = f"backfill:support_ticket_created:{t.id}"
            if not await AnalyticsBackfill._exists(db, create_key):
                event = AnalyticsEvent(
                    workspace_id=t.workspace_id,
                    conversation_id=t.conversation_id,
                    customer_id=t.customer_id,
                    event_type=AnalyticsEventType.SUPPORT_TICKET_CREATED.value,
                    event_metadata={"priority": t.priority, "status": t.status, "issue_type": t.issue_type},
                    idempotency_key=create_key,
                    schema_version=1,
                    created_at=t.created_at,
                )
                db.add(event)
                inserted += 1

            if t.status in ("resolved", "closed"):
                resolve_key = f"backfill:support_ticket_resolved:{t.id}"
                if not await AnalyticsBackfill._exists(db, resolve_key):
                    event = AnalyticsEvent(
                        workspace_id=t.workspace_id,
                        conversation_id=t.conversation_id,
                        customer_id=t.customer_id,
                        event_type=AnalyticsEventType.SUPPORT_TICKET_RESOLVED.value,
                        idempotency_key=resolve_key,
                        schema_version=1,
                        created_at=t.last_interaction_at or t.created_at,
                    )
                    db.add(event)
                    inserted += 1

        return inserted

    @staticmethod
    async def _backfill_customer_care(db: AsyncSession, workspace_id: UUID | None) -> int:
        filters = []
        if workspace_id:
            filters.append(CustomerCareCase.workspace_id == workspace_id)

        stmt = select(CustomerCareCase).where(*filters)
        result = await db.execute(stmt)
        cases = result.scalars().all()

        inserted = 0
        for c in cases:
            create_key = f"backfill:customer_care_case_created:{c.id}"
            if not await AnalyticsBackfill._exists(db, create_key):
                event = AnalyticsEvent(
                    workspace_id=c.workspace_id,
                    conversation_id=c.conversation_id,
                    customer_id=c.customer_id,
                    event_type=AnalyticsEventType.CUSTOMER_CARE_CASE_CREATED.value,
                    event_metadata={
                        "complaint_type": c.complaint_type,
                        "sentiment": c.sentiment,
                        "refund_requested": c.refund_requested,
                    },
                    idempotency_key=create_key,
                    schema_version=1,
                    created_at=c.created_at,
                )
                db.add(event)
                inserted += 1

            if c.current_stage in ("resolved", "closed"):
                close_key = f"backfill:customer_care_case_closed:{c.id}"
                if not await AnalyticsBackfill._exists(db, close_key):
                    event = AnalyticsEvent(
                        workspace_id=c.workspace_id,
                        conversation_id=c.conversation_id,
                        customer_id=c.customer_id,
                        event_type=AnalyticsEventType.CUSTOMER_CARE_CASE_CLOSED.value,
                        idempotency_key=close_key,
                        schema_version=1,
                        created_at=c.updated_at or c.created_at,
                    )
                    db.add(event)
                    inserted += 1

        return inserted

    @staticmethod
    async def _exists(db: AsyncSession, idempotency_key: str) -> bool:
        stmt = select(AnalyticsEvent.id).where(
            AnalyticsEvent.idempotency_key == idempotency_key
        ).limit(1)
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None
