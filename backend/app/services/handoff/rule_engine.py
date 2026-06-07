import logging
from typing import Optional
from datetime import datetime, timezone

from backend.app.schemas.handoff import AgentType, HandoffReason, IntentType, HandoffDecision

logger = logging.getLogger(__name__)

class HandoffRuleEngine:
    """
    Evaluates router intents and current state to deterministically 
    decide if an agent handoff should occur.
    """

    @staticmethod
    def evaluate(
        active_agent: Optional[AgentType],
        primary_intent: str,
        cooldown_until: Optional[str] = None,
        previous_agent: Optional[AgentType] = None
    ) -> HandoffDecision:
        # 1. Enforce cooldown (Loop Prevention)
        if cooldown_until:
            try:
                cooldown_dt = datetime.fromisoformat(cooldown_until)
                if datetime.now(timezone.utc) < cooldown_dt:
                    logger.info("Loop prevention cooldown active. Blocking handoff.")
                    return HandoffDecision(
                        should_handoff=False,
                        reason=HandoffReason.LOOP_PREVENTION,
                        context_summary="Handoff suppressed due to active loop cooldown."
                    )
            except ValueError:
                pass

        # 2. Parse Intent safely
        try:
            intent = IntentType(primary_intent)
        except ValueError:
            intent = IntentType.UNKNOWN

        target_agent = active_agent
        reason = None

        # 3. Deterministic Routing Rules
        if intent == IntentType.TROUBLESHOOT:
            target_agent = AgentType.SUPPORT
            reason = HandoffReason.TECHNICAL_ISSUE
        elif intent == IntentType.BUY_PRODUCT:
            target_agent = AgentType.SALES
            reason = HandoffReason.SALES_INQUIRY
        elif intent in [IntentType.REFUND, IntentType.COMPLAIN]:
            target_agent = AgentType.CUSTOMER_CARE
            reason = HandoffReason.COMPLAINT if intent == IntentType.COMPLAIN else HandoffReason.REFUND_REQUEST

        # 3.5 Detect Transition Oscillation (Ping-Pong)
        if target_agent and previous_agent and target_agent == previous_agent and target_agent != active_agent:
            logger.info(f"Ping-pong oscillation detected: {previous_agent.value} -> {active_agent.value} -> {target_agent.value}. Blocking.")
            return HandoffDecision(
                should_handoff=False,
                reason=HandoffReason.LOOP_PREVENTION,
                context_summary="Handoff suppressed due to oscillation loop detection."
            )

        # 4. No-op if target is already active
        if target_agent and target_agent != active_agent:
            return HandoffDecision(
                should_handoff=True,
                to_agent=target_agent,
                reason=reason,
                context_summary=f"Routing to {target_agent.value} based on intent {intent.value}."
            )
        
        return HandoffDecision(should_handoff=False)
