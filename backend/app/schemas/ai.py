from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AIRequest(BaseModel):
    """
    Standard request payload for generating an AI response via AIService.
    """
    user_query: str = Field(description="The latest input from the user")
    system_prompt: str = Field(description="The system instruction defining the persona/rules")
    conversation_history: Optional[List[str]] = Field(
        default_factory=list, description="List of previous conversation turns"
    )
    rag_context: Optional[str] = Field(
        default=None, description="Injected RAG context string, if applicable"
    )
    response_schema: Optional[Any] = Field(
        default=None, description="Optional Pydantic BaseModel class for structured output"
    )


class AIResponse(BaseModel):
    """
    Standardized AI output envelope.
    """
    content: str = Field(description="The natural language output")
    structured_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Parsed structured JSON if response_schema was provided"
    )
    latency_ms: float = Field(default=0.0, description="Latency of the LLM call")
    tokens_used: int = Field(default=0, description="Total tokens consumed (prompt + completion)")
    sources: List[Dict[str, Any]] = Field(
        default_factory=list, description="Source attribution passed through from RAG context"
    )
    error: Optional[str] = Field(default=None, description="Error message, if any")
