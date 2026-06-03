from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import Optional, Dict, Any
from backend.app.models.workspace import Workspace
from backend.app.models.user import User

class WorkspaceRepository:
    @staticmethod
    async def create(db: AsyncSession, *, name: str, industry: Optional[str] = None) -> Workspace:
        db_obj = Workspace(name=name, industry=industry)
        db.add(db_obj)
        await db.flush()
        return db_obj

    @staticmethod
    async def get(db: AsyncSession, workspace_id: UUID) -> Optional[Workspace]:
        result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
        return result.scalars().first()

    @staticmethod
    async def update(db: AsyncSession, *, db_obj: Workspace, obj_in: Dict[str, Any]) -> Workspace:
        for field in obj_in:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_in[field])
        db.add(db_obj)
        await db.flush()
        return db_obj

    @staticmethod
    async def get_stats(db: AsyncSession, workspace_id: UUID) -> Dict[str, int]:
        # Count users in this workspace
        user_count_result = await db.execute(
            select(User).where(User.workspace_id == workspace_id)
        )
        users_count = len(user_count_result.scalars().all())
        
        # Placeholders for other entities (since their tables aren't created yet)
        return {
            "users_count": users_count,
            "customers_count": 0,
            "conversations_count": 0,
            "tickets_count": 0,
            "documents_count": 0
        }
