import os
import logging
from typing import Optional
from google import genai

from backend.app.core.agents.base_agent import BaseAgent, AgentResponse
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class CustomerCareAgent(BaseAgent):
    """
    Customer Care Agent — Highest empathy level.

    Behavior (Master Build Instructions §CUSTOMER CARE AGENT RULES):
    - Acknowledge frustration
    - Explain next steps
    - Refund Support, Complaints, Retention
    - Empathy-first behavior layer

    Must NOT:
    - Ignore customer emotions
    - Respond coldly
    """

    SYSTEM_PROMPT = """You are the OmniFlow Customer Care Agent — a relationship management specialist. You handle emotionally charged situations, refunds, complaints, and customer retention.

Your primary directive is to use an Empathy-First behavior layer. Always de-escalate, listen, and ensure the customer feels heard and valued.

Behavior rules:
- **Empathy-First:** Always acknowledge the customer's frustration or emotion BEFORE offering any solutions. Apologize sincerely when appropriate.
- **Refund Support:** Handle refund and cancellation requests smoothly, but strictly enforce the policies provided in the knowledge base context. Do not promise a refund if the policy prohibits it.
- **Retention:** When a customer wants to cancel, politely seek to understand their reason. Offer reasonable alternatives (like pausing the account or downgrading) if the context allows.
- **Complaints:** Never argue with the customer, assign blame, or become defensive. Use warm, human language — never corporate jargon.
- **Action-Oriented:** Explain exactly what will happen next in clear, simple terms.

Strict prohibitions:
- NEVER ignore or minimize customer emotions.
- NEVER respond coldly or with generic template language.
- NEVER promise a refund or concession that violates the provided company policies.

If you cannot resolve the issue or the customer demands management, assure them you are personally escalating it and explain the timeline.

Keep responses warm, genuine, and action-oriented."""

    _client: Optional[genai.Client] = None

    @property
    def agent_type(self) -> str:
        return "customer_care"

    @classmethod
    def _get_client(cls) -> genai.Client:
        if cls._client is None:
            api_key = getattr(settings, "GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not configured.")
            cls._client = genai.Client(api_key=api_key)
        return cls._client

    async def respond(
        self,
        message: str,
        conversation_history: Optional[list[str]] = None,
        context: Optional[dict] = None
    ) -> AgentResponse:
        client = self._get_client()

        # Build context block from RAG knowledge chunks if provided (e.g. return policies)
        context_block = ""
        if context:
            if context.get("rag_chunks"):
                chunks_text = "\n\n".join(context["rag_chunks"])
                context_block += f"\n\n--- COMPANY POLICIES & CONTEXT ---\n{chunks_text}\n----------------------------------\n"
            if context.get("system_note"):
                context_block += f"\n\n{context.get('system_note')}\n"

        system_with_context = self.SYSTEM_PROMPT + context_block

        contents = [{"role": "user", "parts": [{"text": system_with_context}]},
                    {"role": "model", "parts": [{"text": "Understood. I am the Customer Care Agent. I will prioritize empathy and follow company policy."}]}]

        if conversation_history:
            for i, turn in enumerate(conversation_history[-8:]):
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
                metadata={
                    "model": "gemini-2.0-flash",
                    "rag_used": bool(context_block)
                }
            )
        except Exception as e:
            logger.error(f"CustomerCareAgent failed to generate response: {e}")
            return AgentResponse(
                content="I completely understand your frustration, and I'm truly sorry for this experience. Let me look into this right away and make sure we get this resolved for you.",
                agent_type=self.agent_type
            )
