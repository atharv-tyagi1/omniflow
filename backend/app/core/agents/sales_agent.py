import os
import logging
from typing import Optional
from google import genai

from backend.app.core.agents.base_agent import BaseAgent, AgentResponse
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class SalesAgent(BaseAgent):
    """
    Sales Agent — Consultative and product-focused.

    Behavior (Master Build Instructions §SALES AGENT RULES):
    - Discover customer needs
    - Recommend products
    - Handle objections
    - Qualify leads

    Must NOT:
    - Invent pricing
    - Invent product details
    """

    SYSTEM_PROMPT = """You are the OmniFlow Sales Agent — a consultative, product-focused AI sales specialist.

Your role is to qualify leads, help customers understand products, discover their true needs, and guide them toward the right solution based strictly on the provided knowledge base context.

Behavior rules:
- **Lead Qualification:** Ask clarifying questions to discover what the customer truly needs, their budget, or timeline if appropriate.
- **Product Discovery:** Understand the customer's pain points and match them to our capabilities.
- **Recommendations:** Recommend relevant products or services ONLY based on the provided context docs. Do not invent products.
- **Objection Handling:** Handle objections professionally, with confidence, and emphasize value.
- Be warm, engaging, and build trust. Keep responses concise and action-oriented.

Strict prohibitions:
- NEVER invent pricing figures not explicitly stated in your context.
- NEVER invent product specifications or features.
- NEVER make commitments that the business cannot keep.
- If you don't know a specific detail, say: "Let me connect you with our team for exact details."
"""

    _client: Optional[genai.Client] = None

    @property
    def agent_type(self) -> str:
        return "sales"

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

        # Build context block from RAG knowledge chunks if provided
        context_block = ""
        if context:
            if context.get("rag_chunks"):
                chunks_text = "\n\n".join(context["rag_chunks"])
                context_block += f"\n\nPRODUCT KNOWLEDGE & CONTEXT:\n{chunks_text}\n"
            if context.get("system_note"):
                context_block += f"\n\n{context.get('system_note')}\n"

        system_with_context = self.SYSTEM_PROMPT + context_block

        contents = [{"role": "user", "parts": [{"text": system_with_context}]},
                    {"role": "model", "parts": [{"text": "Understood. I am the Sales Agent. How can I help?"}]}]

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
            logger.error(f"SalesAgent failed to generate response: {e}")
            return AgentResponse(
                content="I'm here to help with any questions about our products. Could you tell me more about what you're looking for?",
                agent_type=self.agent_type
            )
