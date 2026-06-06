from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal

from backend.app.models.customer_care_case import CustomerCareCase
from backend.app.repositories.customer_care_repository import customer_care_case_repo
from backend.app.schemas.customer_care import CustomerCareStage, ComplaintType, CustomerSentiment
from backend.app.core.exceptions import NotFoundError

class CustomerCareService:
    @staticmethod
    async def get_or_create_case_for_conversation(
        db: AsyncSession,
        workspace_id: UUID,
        customer_id: UUID,
        conversation_id: UUID,
    ) -> CustomerCareCase:
        """Idempotently load an active case or create a new one."""
        
        # Terminal stages
        terminal_stages = [CustomerCareStage.RESOLVED.value, CustomerCareStage.CLOSED.value]
        
        stmt = select(CustomerCareCase).where(
            CustomerCareCase.workspace_id == workspace_id,
            CustomerCareCase.conversation_id == conversation_id,
            CustomerCareCase.current_stage.not_in(terminal_stages)
        ).limit(1)
        
        result = await db.execute(stmt)
        active_case = result.scalars().first()
        
        if active_case:
            return active_case
            
        # Create a new case if no active one exists
        return await customer_care_case_repo.create(
            db,
            workspace_id=workspace_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            current_stage=CustomerCareStage.ACKNOWLEDGED.value
        )
        
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
        escalation_reason: str | None = None
    ) -> CustomerCareCase:
        
        case = await customer_care_case_repo.get_by_id(db, case_id, workspace_id)
        if not case:
            raise NotFoundError("Customer care case not found")
            
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
        
        if escalation_reason:
            update_data["escalation_reason"] = escalation_reason
            
        return await customer_care_case_repo.update(db, db_obj=case, obj_in=update_data)
