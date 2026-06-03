from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from backend.app.core.database import get_db
from backend.app.core.security import decode_token
from backend.app.core.exceptions import AuthenticationError, AuthorizationError
from backend.app.repositories.user_repository import UserRepository
from backend.app.models.user import User

security_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not credentials:
        raise AuthenticationError("Missing authorization header")
        
    token = credentials.credentials
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise AuthenticationError("Invalid or expired authentication token")
        
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationError("Invalid authentication token payload")
        
    user = await UserRepository.get_by_id(db, UUID(user_id_str))
    if not user:
        raise AuthenticationError("User not found")
        
    if user.status != "active":
        raise AuthenticationError("User account is inactive")
        
    return user
