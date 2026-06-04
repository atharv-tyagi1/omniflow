from typing import List, Optional

class PromptBuilder:
    """
    Utility class for safely and consistently constructing context-aware prompts
    for the AI orchestration layer.
    """

    @staticmethod
    def build_prompt(
        system_prompt: str,
        user_query: str,
        conversation_history: Optional[List[str]] = None,
        rag_context: Optional[str] = None,
        max_history_turns: int = 6
    ) -> str:
        """
        Assembles a comprehensive prompt for the Gemini model.
        
        Args:
            system_prompt: The primary instructions for the AI persona.
            user_query: The immediate user input.
            conversation_history: List of previous conversation turns (e.g. "User: Hi", "AI: Hello").
            rag_context: Injected knowledge base context.
            max_history_turns: Number of recent history turns to retain to avoid token bloat.
            
        Returns:
            str: The fully assembled prompt string.
        """
        parts = [
            "=== SYSTEM INSTRUCTIONS ===",
            system_prompt.strip()
        ]
        
        if rag_context and rag_context.strip():
            parts.extend([
                "\n=== KNOWLEDGE BASE CONTEXT ===",
                "Use the following provided context to inform your answer. If the answer is not contained in the context, say so.",
                rag_context.strip()
            ])
            
        if conversation_history and len(conversation_history) > 0:
            recent_history = conversation_history[-max_history_turns:]
            parts.extend([
                "\n=== CONVERSATION HISTORY ===",
                "\n".join(recent_history)
            ])
            
        parts.extend([
            "\n=== CURRENT REQUEST ===",
            f"User: {user_query.strip()}"
        ])
        
        return "\n".join(parts)
