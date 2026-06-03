from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.auth_service import AuthService
from backend.app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    UserResponse,
    TokenResponse,
)
from backend.app.core.response import success_response


class AuthController:
    @staticmethod
    async def signup(db: AsyncSession, signup_data: SignupRequest) -> dict:
        result = await AuthService.signup(db, signup_data)

        # Serialize user response
        user_resp = UserResponse.model_validate(result["user"])
        tokens = TokenResponse(
            access_token=result["access_token"], refresh_token=result["refresh_token"]
        )

        return success_response(
            {
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token,
                "token_type": tokens.token_type,
                "user": user_resp.model_dump(),
            }
        )

    @staticmethod
    async def login(db: AsyncSession, login_data: LoginRequest) -> dict:
        result = await AuthService.login(db, login_data)

        user_resp = UserResponse.model_validate(result["user"])
        tokens = TokenResponse(
            access_token=result["access_token"], refresh_token=result["refresh_token"]
        )

        return success_response(
            {
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token,
                "token_type": tokens.token_type,
                "user": user_resp.model_dump(),
            }
        )

    @staticmethod
    async def refresh_tokens(db: AsyncSession, refresh_token: str) -> dict:
        result = await AuthService.refresh_tokens(db, refresh_token)

        tokens = TokenResponse(
            access_token=result["access_token"], refresh_token=result["refresh_token"]
        )

        return success_response(tokens.model_dump())
