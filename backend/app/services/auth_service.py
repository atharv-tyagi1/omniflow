from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.user_repository import UserRepository
from backend.app.repositories.workspace_repository import WorkspaceRepository
from backend.app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from backend.app.core.exceptions import AuthenticationError, BusinessRuleError
from backend.app.schemas.auth import SignupRequest, LoginRequest
from uuid import UUID


class AuthService:
    @staticmethod
    async def signup(db: AsyncSession, signup_data: SignupRequest) -> dict:
        # Check if email already registered
        existing_user = await UserRepository.get_by_email(db, signup_data.email)
        if existing_user:
            raise BusinessRuleError("Email is already registered")

        # 1. Create workspace
        workspace = await WorkspaceRepository.create(
            db, name=signup_data.workspace_name
        )

        # 2. Hash password
        pwd_hash = hash_password(signup_data.password)

        # 3. Create user (role: owner for signup)
        user = await UserRepository.create(
            db,
            email=signup_data.email,
            full_name=signup_data.full_name,
            password_hash=pwd_hash,
            role="owner",
            workspace_id=workspace.id,
        )

        # Generate tokens
        token_data = {
            "sub": str(user.id),
            "workspace_id": str(user.workspace_id),
            "role": user.role,
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user,
        }

    @staticmethod
    async def login(db: AsyncSession, login_data: LoginRequest) -> dict:
        user = await UserRepository.get_by_email(db, login_data.email)
        if not user:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(login_data.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        if user.status != "active":
            raise AuthenticationError("User account is inactive")

        # Generate tokens
        token_data = {
            "sub": str(user.id),
            "workspace_id": str(user.workspace_id),
            "role": user.role,
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user,
        }

    @staticmethod
    async def refresh_tokens(db: AsyncSession, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthenticationError("Invalid or expired refresh token")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationError("Invalid token payload")

        user = await UserRepository.get_by_id(db, UUID(user_id_str))
        if not user or user.status != "active":
            raise AuthenticationError(
                "User associated with token not found or inactive"
            )

        # Generate new tokens
        token_data = {
            "sub": str(user.id),
            "workspace_id": str(user.workspace_id),
            "role": user.role,
        }

        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        return {"access_token": new_access_token, "refresh_token": new_refresh_token}
