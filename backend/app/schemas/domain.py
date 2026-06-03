from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


# --- Conversations ---

class ConversationCreate(BaseModel):
    customer_id: UUID
    channel: str = "web"

class MessageCreate(BaseModel):
    sender_type: str
    content: str
    message_type: str = "text"


# --- Documents (Knowledge Base) ---

class DocumentUpload(BaseModel):
    name: str
    file_type: str
    file_url: str

class SearchQuery(BaseModel):
    query: str
    limit: int = 5


# --- Datasets ---

class DatasetUpload(BaseModel):
    name: str
    file_url: str
    row_count: Optional[int] = None
    column_count: Optional[int] = None

class DatasetQueryRequest(BaseModel):
    question: str


# --- Workflows ---

class WorkflowCreate(BaseModel):
    name: str
    trigger_type: str
