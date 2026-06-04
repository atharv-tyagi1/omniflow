from backend.app.schemas.agent import AgentContext


class AgentPromptBuilder:
    """Centralized prompt assembly for all AI Agents."""

    @staticmethod
    def build_system_prompt(
        agent_name: str,
        base_instructions: str,
        context: AgentContext
    ) -> str:
        """
        Assembles the definitive system prompt containing core instructions,
        context injections, and strict output requirements.
        """
        prompt_parts = [
            f"You are the {agent_name} for OmniFlow.",
            base_instructions,
            "\n--- CONTEXT ---",
        ]

        if context.workspace_context:
            prompt_parts.append(f"Workspace Settings: {context.workspace_context}")
        
        if context.customer_context:
            prompt_parts.append(f"Customer Profile: {context.customer_context}")

        if context.rag_context:
            prompt_parts.append("Knowledge Base Context:")
            prompt_parts.extend([f"- {c}" for c in context.rag_context])

        if context.conversation_state:
            prompt_parts.append(f"Conversation State: {context.conversation_state}")
            
        prompt_parts.append("\n--- SCHEMA REQUIREMENTS ---")
        prompt_parts.append(
            "You must respond using the exact structured JSON schema provided. "
            "Set `handoff_recommended` to true ONLY if you cannot resolve the issue and need another agent. "
            "Set `requires_human` to true ONLY if explicit human escalation is requested or mandatory."
        )

        return "\n".join(prompt_parts)

    @staticmethod
    def format_conversation_history(history: list[dict]) -> str:
        """Formats standard conversation history."""
        if not history:
            return ""
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
