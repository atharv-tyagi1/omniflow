from typing import Any, Generic, TypeVar, Optional, Literal
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")

class PublicResponse(BaseModel, Generic[DataT]):
    """Standardized response envelope for all public API responses."""
    success: bool
    data: Optional[DataT] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: Optional[dict[str, Any]] = None

class PublicChatRequest(BaseModel):
    """Payload for submitting a chat message to OmniFlow."""
    external_customer_id: str = Field(..., description="Your internal user ID")
    customer_name: str = Field(..., description="Name of the customer")
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    message: str = Field(..., description="The message from the customer")
    response_mode: Literal["sync", "async"] = Field(default="sync", description="Execution mode")
    conversation_external_id: Optional[str] = Field(default=None, description="Optional custom conversation ID")

class PublicChatResponse(BaseModel):
    """Payload for a synchronous chat response."""
    conversation_id: str
    message_id: str
    content: str
    agent_name: Optional[str] = None

class PublicAsyncJobResponse(BaseModel):
    """Payload for an asynchronous execution acknowledgement."""
    job_id: str
    status_url: str

class PublicAsyncJobStatus(BaseModel):
    """Payload for checking async job status."""
    job_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None

class PublicCustomerSchema(BaseModel):
    """Basic customer payload."""
    id: str
    external_id: Optional[str] = None
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str

class PublicConversationSchema(BaseModel):
    """Basic conversation payload."""
    id: str
    customer_id: str
    external_id: Optional[str] = None
    channel: str
    status: str
    started_at: str

class PublicWebhookConfig(BaseModel):
    """Webhook registration payload."""
    source: str
    url: str
