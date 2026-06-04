from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime


class TicketCreate(BaseModel):
    customer_id: UUID
    conversation_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[str] = Field("medium", max_length=20)


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, max_length=20)
    assigned_to: Optional[UUID] = None


class TicketResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    customer_id: UUID
    conversation_id: UUID
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    assigned_to: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True
