from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from backend.app.core.database import get_db
from backend.app.middleware.auth import get_current_user
from backend.app.middleware.workspace_guard import get_current_workspace_id, require_admin, require_capability
from backend.app.models.user import User
from backend.app.services.public.public_api_service import PublicApiService

router = APIRouter(
    prefix="/api-keys", 
    tags=["api_keys"],
    dependencies=[
        Depends(require_admin),
        Depends(require_capability("apiKeys"))
    ]
)

# --- Schemas ---

class ApiKeyScopeResponse(BaseModel):
    scope_name: str

class ApiKeyResponse(BaseModel):
    id: UUID = Field(..., description="Unique identifier of the API Key")
    name: str = Field(..., description="Human-readable name of the API key")
    prefix: str = Field(..., description="Prefix of the key (e.g. of_live_...)")
    status: str = Field(..., description="Status of the API key (e.g. active, revoked)")
    request_count: int = Field(..., description="Total number of requests made with this key")
    rate_limit_tier: str = Field(..., description="Rate limit tier associated with this key")
    last_used_at: Optional[datetime] = Field(None, description="Timestamp of last usage")
    created_at: datetime = Field(..., description="Timestamp when the key was created")
    
    class Config:
        from_attributes = True

class ApiKeyListResponse(BaseModel):
    items: List[ApiKeyResponse]
    total: int
    page: int
    limit: int

class CreateApiKeyRequest(BaseModel):
    name: str = Field(..., description="Name to identify the API key", example="Production Integration")
    scopes: List[str] = Field(..., description="List of canonical scopes", example=["analytics.read"])

class CreateApiKeyResponse(BaseModel):
    key_secret: str = Field(..., description="The plaintext API Key secret. THIS IS ONLY RETURNED ONCE.")
    
class RotateApiKeyRequest(BaseModel):
    reason: Optional[str] = Field(None, description="Optional reason for rotation")

class RotateApiKeyResponse(BaseModel):
    new_key_secret: str = Field(..., description="The new plaintext API Key secret. THIS IS ONLY RETURNED ONCE.")

class RevokeApiKeyResponse(BaseModel):
    success: bool = Field(..., description="Whether the key was successfully revoked")

# --- Endpoints ---

@router.get("", response_model=ApiKeyListResponse)
async def list_api_keys(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status (e.g., active, revoked)"),
    search: Optional[str] = Query(None, description="Filter by name (ilike)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """
    List all API keys for the current workspace with pagination and filtering.
    Note: Sensitive usage metadata (last_ip, last_user_agent) is omitted from the response.
    """
    keys, total = await PublicApiService.list_api_keys(
        db=db,
        workspace_id=workspace_id,
        page=page,
        limit=limit,
        status=status,
        search=search
    )
    
    # Exclude sensitive attributes by relying on the strict Pydantic model
    return ApiKeyListResponse(
        items=[ApiKeyResponse.model_validate(k) for k in keys],
        total=total,
        page=page,
        limit=limit
    )


@router.post("", response_model=CreateApiKeyResponse)
async def create_api_key(
    req: CreateApiKeyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """
    Creates a new API key and assigns scopes.
    Returns the plaintext secret exactly once.
    """
    try:
        plain_key = await PublicApiService.create_api_key(
            db=db,
            workspace_id=workspace_id,
            user_id=current_user.id,
            name=req.name,
            scopes=req.scopes
        )
        return CreateApiKeyResponse(key_secret=plain_key)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{api_key_id}/rotate", response_model=RotateApiKeyResponse)
async def rotate_api_key(
    api_key_id: UUID,
    req: RotateApiKeyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """
    Rotates an API key.
    Soft revokes the old key and generates a new key under the same identity context.
    Returns the new plaintext secret exactly once.
    """
    try:
        plain_key = await PublicApiService.rotate_api_key(
            db=db,
            workspace_id=workspace_id,
            api_key_id=api_key_id,
            rotated_by_user_id=current_user.id,
            reason=req.reason
        )
        return RotateApiKeyResponse(new_key_secret=plain_key)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{api_key_id}", response_model=RevokeApiKeyResponse)
async def revoke_api_key(
    api_key_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """
    Soft revokes an API key idempotently.
    Immediately invalidates associated auth caches.
    Returns 200 OK even if the key is not found or already revoked.
    """
    try:
        await PublicApiService.revoke_api_key(
            db=db,
            workspace_id=workspace_id,
            api_key_id=api_key_id,
            revoked_by_user_id=current_user.id
        )
        return RevokeApiKeyResponse(success=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
