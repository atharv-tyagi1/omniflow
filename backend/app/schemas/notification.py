from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime


class NotificationResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    title: str
    message: Optional[str] = None
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
