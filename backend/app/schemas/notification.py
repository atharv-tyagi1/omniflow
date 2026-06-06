from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)
