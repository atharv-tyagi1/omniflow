from fastapi import Depends
from uuid import UUID
from typing import List
from backend.app.middleware.auth import get_current_user
from backend.app.models.user import User
from backend.app.core.exceptions import AuthorizationError

def get_current_workspace_id(current_user: User = Depends(get_current_user)) -> UUID:
    """
    FastAPI dependency that returns the authenticated user's workspace_id.
    This guarantees that the user has a valid workspace context.
    """
    return current_user.workspace_id

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise AuthorizationError(
                f"Role '{current_user.role}' is not authorized. Required one of: {self.allowed_roles}"
            )
        return current_user

# Predefined role dependencies
require_owner = RoleChecker(["owner"])
require_admin = RoleChecker(["owner", "admin"])
