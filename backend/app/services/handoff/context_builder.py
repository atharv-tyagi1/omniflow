from typing import Optional, List
from backend.app.schemas.handoff import ConversationHandoffStateV1

class HandoffContextBuilder:
    """
    Constructs a safely bounded context object for target agents to prevent token bloat.
    """

    @staticmethod
    def build_transition_context(
        state: ConversationHandoffStateV1,
        recent_messages: List[str],
        max_turns: int = 5
    ) -> dict:
        """
        Builds a bounded context dictionary for the target agent.
        Only keeps the last N turns of history, substituting a generic placeholder for older items.
        """
        total_turns = len(recent_messages)
        if total_turns > max_turns:
            summary_buffer = state.handoff_summary or "Previous conversation context has been summarized."
            bounded_history = [f"[Rolling Summary: {summary_buffer}]"] + recent_messages[-max_turns:]
        else:
            bounded_history = recent_messages[:]
        
        prev_agent = state.previous_agent.value if state.previous_agent else "a different team"
        reason_text = state.handoff_summary or "Continuing support."
        
        context = {
            "system_note": (
                f"SYSTEM NOTE: The customer was just transferred to you from '{prev_agent}'. "
                f"Context: {reason_text}. "
                f"Acknowledge this transition naturally and continue assisting them."
            ),
            "unresolved_intent": state.unresolved_intent.value if state.unresolved_intent else "unknown",
            "bounded_history": bounded_history
        }
        return context
