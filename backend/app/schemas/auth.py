from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from typing import Optional


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    workspace_name: str = Field(..., min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """
    API response for user info. workspace_id and role are not on the User ORM
    model anymore — they come from workspace_members and are injected by the
    controller/service layer.
    """
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    workspace_id: UUID
    status: str
    avatar_url: Optional[str] = None
