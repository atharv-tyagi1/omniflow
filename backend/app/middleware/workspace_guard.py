from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.middleware.auth import get_current_user
from backend.app.core.database import get_db
from backend.app.core.security import decode_token
from backend.app.core.exceptions import AuthorizationError, AuthenticationError
from backend.app.models.user import User
from backend.app.repositories.workspace_member_repository import WorkspaceMemberRepository

security_scheme = HTTPBearer(auto_error=False)


async def get_current_workspace_id(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> UUID:
    """
    Extract the active workspace_id from the JWT token.
    The workspace context is embedded in the token during login/signup.
    """
    if not credentials:
        raise AuthenticationError("Missing authorization header")

    from backend.app.core.security import decode_token
    payload = decode_token(credentials.credentials)
    if not payload:
        raise AuthenticationError("Invalid or expired token")

    workspace_id_str = payload.get("workspace_id")
    if not workspace_id_str:
        raise AuthorizationError("No workspace context found in token")

    return UUID(workspace_id_str)


class RoleChecker:
    """
    Dependency that verifies the authenticated user's role within their
    active workspace meets the minimum required role.
    Roles are now derived from workspace_members, encoded in the JWT.
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        if not credentials:
            raise AuthenticationError("Missing authorization header")

        payload = decode_token(credentials.credentials)
        if not payload:
            raise AuthenticationError("Invalid or expired token")

        workspace_id_str = payload.get("workspace_id")
        if not workspace_id_str:
            raise AuthorizationError("No workspace context found in token")

        # Verify membership exists and get live role from DB
        membership = await WorkspaceMemberRepository.get_by_user_and_workspace(
            db, current_user.id, UUID(workspace_id_str)
        )
        if not membership:
            raise AuthorizationError("User is not a member of this workspace")

        if membership.role not in self.allowed_roles:
            raise AuthorizationError(
                f"Role '{membership.role}' is not authorized. Required one of: {self.allowed_roles}"
            )
        return current_user


# Predefined role dependencies
require_owner = RoleChecker(["owner"])
require_admin = RoleChecker(["owner", "admin"])
require_manager = RoleChecker(["owner", "admin", "manager"])


def require_capability(capability_name: str):
    """
    Dependency that verifies the active workspace has access to a specific capability
    based on its billing plan.
    """
    async def _check_capability(
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
        db: AsyncSession = Depends(get_db),
    ) -> UUID:
        workspace_id = await get_current_workspace_id(credentials)
        
        # Load the workspace
        from backend.app.repositories.workspace_repository import WorkspaceRepository
        workspace = await WorkspaceRepository.get(db, workspace_id)
        if not workspace:
            raise AuthorizationError("Workspace not found")
            
        # Define capability plan mapping
        capability_matrix = {
            "apiKeys": ["pro", "enterprise", "scale"],
            # add other capabilities here as needed
        }
        
        allowed_plans = capability_matrix.get(capability_name, [])
        
        if workspace.plan not in allowed_plans and "all" not in allowed_plans:
            # If the capability is not in the allowed plans for the workspace
            # For this MVP, we might just allow it if not strictly defined, or block.
            # Since we must enforce it, block if it's strictly defined and not matched.
            if allowed_plans:
                raise AuthorizationError(f"Capability '{capability_name}' requires plan upgrade.")
                
        return workspace_id
        
    return _check_capability
