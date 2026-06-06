from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from typing import Optional


class WorkspaceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)


class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    industry: Optional[str] = None
    plan: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class WorkspaceUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)


class WorkspaceMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    workspace_id: UUID
    role: str
    user_email: str = ""
    user_name: str = ""


class WorkspaceStatsResponse(BaseModel):
    users_count: int
    customers_count: int
    conversations_count: int
    tickets_count: int
    documents_count: int
