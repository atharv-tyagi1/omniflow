from pydantic import BaseModel, Field
from typing import Optional


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    avatar_url: Optional[str] = None


class UserRoleUpdate(BaseModel):
    role: str = Field(..., max_length=50) # owner, admin, manager, member
