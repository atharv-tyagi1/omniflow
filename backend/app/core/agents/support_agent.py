import os
import logging
from typing import Optional
from google import genai

from backend.app.core.agents.base_agent import BaseAgent, AgentResponse
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class SupportAgent(BaseAgent):
    """
    Support Agent — Solution-focused and accurate.

    Behavior (Master Build Instructions §SUPPORT AGENT RULES):
    - Use documentation (RAG context) to answer
    - Verify resolution before closing
    - FAQ Resolution, Troubleshooting, Issue Diagnosis

    Must NOT:
    - Guess solutions
    - Invent troubleshooting steps
    """

    SYSTEM_PROMPT = """You are the OmniFlow Support Agent — a highly technical, precision-focused support specialist.

Your role is to diagnose problems, perform structured troubleshooting, and resolve known issues based strictly on the provided documentation.

Behavior rules:
- **Issue Diagnosis:** If the user's problem is vague, ask targeted diagnostic questions to isolate the root cause before offering a solution.
- **FAQ Resolution:** Prioritize direct answers from the provided knowledge base context for known issues.
- **Structured Troubleshooting:** Provide clear, numbered, step-by-step instructions. Never give the user more than 3 steps at a time to avoid overwhelming them.
- **Context Tracking:** Read the conversation history carefully. Do not ask the user to repeat steps they have already tried or information they have already provided.
- **Verify Resolution:** Always ask if the provided steps resolved their issue before concluding the interaction.

Strict prohibitions:
- NEVER guess at solutions — only provide steps you are confident are correct based on the documentation.
- NEVER invent troubleshooting steps, system paths, or settings that are not explicitly grounded in the provided context.
- If the knowledge base does not contain the answer, cleanly state: "I don't have the exact documentation for that issue. Let me escalate this to our engineering team."

Keep responses highly structured, precise, and polite."""

    _client: Optional[genai.Client] = None

    @property
    def agent_type(self) -> str:
        return "support"

    @classmethod
    def _get_client(cls) -> genai.Client:
        if cls._client is None:
            api_key = getattr(
                settings, "GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY")
            )
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not configured.")
            cls._client = genai.Client(api_key=api_key)
        return cls._client

    async def respond(
        self,
        message: str,
        conversation_history: Optional[list[str]] = None,
        context: Optional[dict] = None,
    ) -> AgentResponse:
        client = self._get_client()

        # Build context block from RAG knowledge chunks if provided
        context_block = ""
        if context:
            if context.get("rag_chunks"):
                chunks_text = "\n\n".join(context["rag_chunks"])
                context_block += f"\n\n--- KNOWLEDGE BASE CONTEXT ---\n{chunks_text}\n------------------------------\n"
            if context.get("system_note"):
                context_block += f"\n\n{context.get('system_note')}\n"

        system_with_context = self.SYSTEM_PROMPT + context_block

        contents = [
            {"role": "user", "parts": [{"text": system_with_context}]},
            {
                "role": "model",
                "parts": [
                    {
                        "text": "Understood. I am the Support Agent. I will strictly follow the documentation and troubleshoot systematically."
                    }
                ],
            },
        ]

        if conversation_history:
            # We pass more history for SupportAgent to allow multi-step tracking
            for i, turn in enumerate(conversation_history[-12:]):
                role = "user" if i % 2 == 0 else "model"
                contents.append({"role": role, "parts": [{"text": turn}]})

        contents.append({"role": "user", "parts": [{"text": message}]})

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
            )
            return AgentResponse(
                content=response.text.strip(),
                agent_type=self.agent_type,
                metadata={"model": "gemini-2.0-flash", "rag_used": bool(context_block)},
            )
        except Exception as e:
            logger.error(f"SupportAgent failed to generate response: {e}")
            return AgentResponse(
                content="I'm here to help resolve your issue. Could you describe exactly what's happening or what steps you've already tried so I can assist you better?",
                agent_type=self.agent_type,
            )
