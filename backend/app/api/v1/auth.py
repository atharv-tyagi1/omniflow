from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.auth import SignupRequest, LoginRequest, UserResponse
from backend.app.controllers.auth_controller import AuthController
from backend.app.middleware.auth import get_current_user
from backend.app.core.security import decode_token
from backend.app.core.exceptions import AuthenticationError
from backend.app.models.user import User
from backend.app.core.response import success_response
from uuid import UUID

router = APIRouter(prefix="/auth", tags=["auth"])
security_scheme = HTTPBearer(auto_error=False)


@router.post("/signup")
async def signup(signup_data: SignupRequest, db: AsyncSession = Depends(get_db)):
    return await AuthController.signup(db, signup_data)


@router.post("/login")
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthController.login(db, login_data)


@router.post("/refresh")
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_db)):
    return await AuthController.refresh_tokens(db, refresh_token)


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    """Return the current authenticated user with their active workspace context."""
    # Extract workspace_id and role from the JWT payload
    workspace_id = None
    role = "member"
    if credentials:
        payload = decode_token(credentials.credentials)
        if payload:
            ws_str = payload.get("workspace_id")
            if ws_str:
                workspace_id = UUID(ws_str)
            role = payload.get("role", "member")

    if not workspace_id:
        raise AuthenticationError("No workspace context in token")

    user_resp = UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        status=current_user.status,
        avatar_url=current_user.avatar_url,
        workspace_id=workspace_id,
        role=role,
    )
    return success_response(user_resp.model_dump())


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # Standard JWT logout is stateless, but we return a clean success envelope
    return success_response({"message": "Successfully logged out"})
