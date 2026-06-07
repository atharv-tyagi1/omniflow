import logging
import time
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timezone

from backend.app.schemas.handoff import HandoffDecision, HandoffStatus, AgentType, ConversationHandoffStateV1
from backend.app.models.handoff import Handoff
from backend.app.models.conversation import Conversation
from backend.app.agents.factory import AgentFactory
from backend.app.schemas.agent import AgentResponse
from backend.app.services.analytics.emitter import AnalyticsEventEmitter
from backend.app.schemas.analytics import AnalyticsEventType

logger = logging.getLogger(__name__)

class HandoffExecutor:
    """
    Executes the deterministic handoff decision via a two-phase commit strategy.
    Dispatches the target agent and updates persistence state safely.
    """

    @staticmethod
    async def execute_handoff(
        db: AsyncSession,
        conversation: Conversation,
        decision: HandoffDecision,
        source_message_id: Optional[str],
        query: str,
        router_metadata: dict,
        bounded_context: dict,
        lineage: Optional[dict] = None
    ) -> AgentResponse:
        
        start_time = time.time()
        
        # 1. Create Pending Handoff Record (Phase 1)
        lineage_data = lineage or {}
        handoff_record = Handoff(
            workspace_id=conversation.workspace_id,
            conversation_id=conversation.id,
            from_agent=conversation.current_agent or AgentType.UNKNOWN.value,
            to_agent=decision.to_agent.value if decision.to_agent else AgentType.UNKNOWN.value,
            reason=decision.reason.value if decision.reason else None,
            status=HandoffStatus.PENDING.value,
            confidence=decision.confidence,
            source_message_id=source_message_id,
            source_entity_type=lineage_data.get("source_entity_type"),
            source_entity_id=lineage_data.get("source_entity_id"),
            target_entity_type=lineage_data.get("target_entity_type"),
            target_entity_id=lineage_data.get("target_entity_id")
        )
        db.add(handoff_record)
        await db.commit()
        await db.refresh(handoff_record)
        
        # Emitting pending telemetry
        HandoffExecutor._emit_telemetry(conversation, handoff_record, "handoff_created", 0)

        # Phase 12: Durable analytics outbox emission
        await AnalyticsEventEmitter.emit(
            db=db,
            workspace_id=conversation.workspace_id,
            event_type=AnalyticsEventType.HANDOFF_CREATED,
            conversation_id=conversation.id,
            customer_id=conversation.customer_id,
            source_agent=handoff_record.from_agent,
            target_agent=handoff_record.to_agent,
            metadata={"reason": handoff_record.reason, "confidence": handoff_record.confidence},
            idempotency_key=f"handoff_created:{handoff_record.id}",
        )

        # 2. Dispatch Target Agent
        try:
            target_agent = AgentFactory.create_agent(handoff_record.to_agent)
            
            # Pass bounded_context directly as router_metadata or merge into context
            merged_metadata = {**router_metadata, **bounded_context}

            response = await target_agent.respond(
                db=db,
                conversation_id=conversation.id,
                customer_id=conversation.customer_id,
                workspace_id=conversation.workspace_id,
                query=query,
                router_metadata=merged_metadata
            )
            
            # 3. Finalize Handoff (Phase 2 - Transactional)
            try:
                handoff_record.status = HandoffStatus.COMPLETED.value
                
                # Update Conversation tracking safely
                conversation.previous_agent = conversation.current_agent
                conversation.current_agent = handoff_record.to_agent
                conversation.handoff_count += 1
                conversation.last_handoff_at = datetime.now(timezone.utc)
                conversation.last_handoff_reason = handoff_record.reason
                
                await db.commit()
            except Exception as commit_err:
                logger.error(f"Handoff state finalization failed: {commit_err}", exc_info=True)
                await db.rollback()
                raise commit_err  # Re-raise to be caught by outer except
            
            latency = int((time.time() - start_time) * 1000)
            HandoffExecutor._emit_telemetry(conversation, handoff_record, "handoff_completed", latency)

            # Phase 12: Durable analytics outbox emission
            await AnalyticsEventEmitter.emit(
                db=db,
                workspace_id=conversation.workspace_id,
                event_type=AnalyticsEventType.HANDOFF_COMPLETED,
                conversation_id=conversation.id,
                customer_id=conversation.customer_id,
                source_agent=handoff_record.from_agent,
                target_agent=handoff_record.to_agent,
                metadata={"reason": handoff_record.reason, "confidence": handoff_record.confidence, "latency_ms": latency},
                idempotency_key=f"handoff_completed:{handoff_record.id}",
            )
            
            return response

        except Exception as e:
            # 4. Rollback / Mark Failed
            logger.error(f"Handoff execution failed: {e}", exc_info=True)
            
            # Use a fresh subtransaction or just update the record to mark it as failed
            try:
                handoff_record.status = HandoffStatus.FAILED.value
                await db.commit()
            except Exception as final_err:
                logger.error(f"Failed to persist FAILED status: {final_err}", exc_info=True)
                await db.rollback()
            
            latency = int((time.time() - start_time) * 1000)
            HandoffExecutor._emit_telemetry(conversation, handoff_record, "handoff_failed", latency)

            # Phase 12: Durable analytics outbox emission
            await AnalyticsEventEmitter.emit(
                db=db,
                workspace_id=conversation.workspace_id,
                event_type=AnalyticsEventType.HANDOFF_FAILED,
                conversation_id=conversation.id,
                customer_id=conversation.customer_id,
                source_agent=handoff_record.from_agent,
                target_agent=handoff_record.to_agent,
                metadata={"reason": handoff_record.reason, "latency_ms": latency},
                idempotency_key=f"handoff_failed:{handoff_record.id}",
            )
            
            # Return graceful escalation response using the active (pre-handoff) agent name if possible
            agent_name = handoff_record.from_agent if handoff_record.from_agent != AgentType.UNKNOWN.value else "system"
            return AgentResponse(
                content="I'm currently experiencing technical difficulties processing your transfer. Please hold while I connect you with a human agent.",
                confidence=0.0,
                agent_name=agent_name,
                handoff_recommended=True,
                requires_human=True,
                sentiment="neutral"
            )

    @staticmethod
    def _emit_telemetry(conversation: Conversation, handoff: Handoff, event_type: str, latency_ms: int):
        event = {
            "event_type": event_type,
            "workspace_id": str(conversation.workspace_id),
            "conversation_id": str(conversation.id),
            "from_agent": handoff.from_agent,
            "to_agent": handoff.to_agent,
            "reason": handoff.reason,
            "confidence": handoff.confidence,
            "latency_ms": latency_ms
        }
        logger.info(f"Handoff Telemetry: {event}")
