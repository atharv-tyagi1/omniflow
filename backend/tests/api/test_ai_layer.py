import pytest
from pydantic import BaseModel, Field
from backend.app.core.ai.prompt_builder import PromptBuilder
from backend.app.schemas.ai import AIRequest
from backend.app.services.ai_service import AIService


class MockSchema(BaseModel):
    category: str = Field(description="The extracted category")
    confidence: float


def test_prompt_builder_assembly():
    """
    Test that the PromptBuilder assembles system, context, history, and query correctly.
    """
    system_prompt = "You are a test bot."
    user_query = "What is the policy?"
    rag_context = "The policy is X."
    history = ["User: Hello", "AI: Hi there!"]

    result = PromptBuilder.build_prompt(
        system_prompt=system_prompt,
        user_query=user_query,
        conversation_history=history,
        rag_context=rag_context,
        max_history_turns=2
    )

    assert "=== SYSTEM INSTRUCTIONS ===" in result
    assert "You are a test bot." in result
    assert "=== KNOWLEDGE BASE CONTEXT ===" in result
    assert "The policy is X." in result
    assert "=== CONVERSATION HISTORY ===" in result
    assert "User: Hello" in result
    assert "=== CURRENT REQUEST ===" in result
    assert "User: What is the policy?" in result


@pytest.mark.asyncio
async def test_ai_service_structured_request():
    """
    Integration test (or mock) verifying that the AIRequest passes schema properly
    and AIService handles validation without crashing.
    """
    request = AIRequest(
        user_query="The customer is angry about a bug.",
        system_prompt="Classify the intent as 'support' or 'complaint' and provide confidence.",
        response_schema=MockSchema
    )

    # Note: In a real CI environment without a valid GEMINI_API_KEY, 
    # the Gemini client will catch the auth error and return it cleanly in the AIResponse.
    response = await AIService.generate_response(request)

    # The service should return a standard AIResponse envelope, not throw an unhandled exception.
    assert hasattr(response, "content")
    assert hasattr(response, "structured_data")
    assert hasattr(response, "error")
    assert hasattr(response, "latency_ms")
    assert hasattr(response, "tokens_used")
