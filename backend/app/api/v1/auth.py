from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from backend.app.core.database import get_db
from backend.app.schemas.auth import SignupRequest, LoginRequest, UserResponse
from backend.app.controllers.auth_controller import AuthController
from backend.app.middleware.auth import get_current_user
from backend.app.models.user import User
from backend.app.core.response import success_response

router = APIRouter(prefix="/auth", tags=["auth"])

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
async def get_me(current_user: User = Depends(get_current_user)):
    user_resp = UserResponse.model_validate(current_user)
    return success_response(user_resp.model_dump())

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # Standard JWT logout is stateless, but we return a clean success envelope
    return success_response({"message": "Successfully logged out"})
