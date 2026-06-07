from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal
import logging
import json

from backend.app.models.customer_care_case import CustomerCareCase
from backend.app.repositories.customer_care_repository import customer_care_case_repo
from backend.app.schemas.customer_care import CustomerCareStage
from backend.app.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)

class CustomerCareService:

    @staticmethod
    def is_terminal_stage(stage: str) -> bool:
        return stage in [CustomerCareStage.RESOLVED.value, CustomerCareStage.CLOSED.value]

    @staticmethod
    def emit_customer_care_event(event_type: str, case: CustomerCareCase, **kwargs):
        """
        Emits a structured JSON event for observability with redaction logic.
        Redacts sensitive PII or raw complaints if required.
        """
        try:
            payload = {
                "event": event_type,
                "workspace_id": str(case.workspace_id),
                "conversation_id": str(case.conversation_id),
                "customer_id": str(case.customer_id),
                "current_stage": case.current_stage,
                "complaint_type": case.complaint_type,
            }
            payload.update(kwargs)

            # Redact escalation reason if it contains sensitive raw text
            if "escalation_reason" in payload and payload["escalation_reason"]:
                reason = payload["escalation_reason"]
                if "requires_human" not in reason and "Invalid" not in reason and "exceeds" not in reason:
                    payload["escalation_reason"] = "[REDACTED]"
                    
            logger.info(json.dumps(payload))
        except Exception as e:
            logger.error(f"Failed to emit customer care event: {e}")

    @staticmethod
    async def get_or_create_case_for_conversation(
        db: AsyncSession,
        workspace_id: UUID,
        customer_id: UUID,
        conversation_id: UUID,
    ) -> CustomerCareCase:
        """Idempotently load an active case or create a new one, safely handling concurrency."""
        
        # Use with_for_update for PostgreSQL to ensure strong concurrency locking
        # SQLite will ignore SKIP LOCKED if it isn't supported, but we keep the IntegrityError retry as fallback
        stmt = select(CustomerCareCase).where(
            CustomerCareCase.workspace_id == workspace_id,
            CustomerCareCase.conversation_id == conversation_id,
            CustomerCareCase.current_stage.not_in([CustomerCareStage.RESOLVED.value, CustomerCareStage.CLOSED.value])
        ).limit(1).with_for_update(skip_locked=True)
        
        result = await db.execute(stmt)
        active_case = result.scalars().first()
        
        if active_case:
            return active_case
            
        # Attempt to create a new case, handling potential concurrency issues via DB unique constraint
        try:
            case = await customer_care_case_repo.create(
                db,
                workspace_id=workspace_id,
                customer_id=customer_id,
                conversation_id=conversation_id,
                current_stage=CustomerCareStage.ACKNOWLEDGED.value
            )
            
            CustomerCareService.emit_customer_care_event("case_created", case)
            return case
            
        except IntegrityError:
            await db.rollback()
            # If an active case was created concurrently, fetch it now
            stmt_retry = select(CustomerCareCase).where(
                CustomerCareCase.workspace_id == workspace_id,
                CustomerCareCase.conversation_id == conversation_id,
                CustomerCareCase.current_stage.not_in([CustomerCareStage.RESOLVED.value, CustomerCareStage.CLOSED.value])
            ).limit(1)
            result = await db.execute(stmt_retry)
            active_case = result.scalars().first()
            if active_case:
                return active_case
            raise RuntimeError("Failed to create or retrieve active customer care case under concurrency.")

    @staticmethod
    async def update_case_context(
        db: AsyncSession,
        workspace_id: UUID,
        case_id: UUID,
        complaint_type: str,
        refund_requested: bool,
        refund_amount_requested: Decimal | None,
        order_id: str | None,
        account_issue_type: str | None,
        sentiment: str,
        current_stage: str,
        resolution_timeline: str | None,
        escalation_reason: str | None = None,
        order_context_total: Decimal | None = None,
        order_context_currency: str | None = None,
        requested_currency: str | None = None
    ) -> tuple[CustomerCareCase, bool, str | None]:
        """
        Updates case context. Returns the updated case, a boolean indicating if requires_human should be forced,
        and an optional escalation reason.
        """
        
        case = await customer_care_case_repo.get_by_id(db, case_id, workspace_id)
        if not case:
            raise NotFoundError("Customer care case not found")
            
        force_human = False
        override_escalation = escalation_reason
        
        # Refund Amount Validation Logic
        if refund_amount_requested is not None:
            if requested_currency and order_context_currency and requested_currency.upper() != order_context_currency.upper():
                refund_amount_requested = None
                force_human = True
                override_escalation = override_escalation or f"Currency mismatch: requested {requested_currency}, order is {order_context_currency}."
            elif refund_amount_requested <= 0:
                refund_amount_requested = None
                force_human = True
                override_escalation = override_escalation or "Invalid refund amount (zero or negative)."
            elif order_context_total is not None and refund_amount_requested > order_context_total:
                refund_amount_requested = None
                force_human = True
                override_escalation = override_escalation or "Requested refund exceeds order total."
        elif refund_requested and not force_human:
            # Explicit check for ambiguous or missing refund amount
            # Do not guess. Just log it for human review if policy requires exact values.
            # We'll allow refund_requested=True with amount=None, but might want human eyes.
            force_human = True
            override_escalation = override_escalation or "Ambiguous or missing refund amount."
                
        update_data = {
            "complaint_type": complaint_type,
            "refund_requested": refund_requested,
            "refund_amount_requested": refund_amount_requested,
            "order_id": order_id,
            "account_issue_type": account_issue_type,
            "sentiment": sentiment,
            "current_stage": current_stage,
            "resolution_timeline": resolution_timeline,
            "last_interaction_at": datetime.now(timezone.utc)
        }
        
        if override_escalation:
            update_data["escalation_reason"] = override_escalation
            
        updated_case = await customer_care_case_repo.update(db, db_obj=case, obj_in=update_data)
        
        # Observability Events
        CustomerCareService.emit_customer_care_event(
            "case_updated", 
            updated_case, 
            escalation_reason=override_escalation
        )
        
        if refund_requested:
            CustomerCareService.emit_customer_care_event("refund_requested", updated_case, refund_amount=str(refund_amount_requested) if refund_amount_requested else None)
            
        if current_stage == CustomerCareStage.REFUND_PENDING.value:
            CustomerCareService.emit_customer_care_event("refund_pending", updated_case)
            
        if force_human or override_escalation:
            CustomerCareService.emit_customer_care_event("escalation_triggered", updated_case, reason=override_escalation)
            
        if CustomerCareService.is_terminal_stage(current_stage):
            CustomerCareService.emit_customer_care_event("case_closed", updated_case)
            
        return updated_case, force_human, override_escalation
