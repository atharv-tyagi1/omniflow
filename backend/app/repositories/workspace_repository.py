from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from uuid import UUID
from typing import Optional, Dict, Any
from backend.app.models.workspace import Workspace
from backend.app.models.workspace_member import WorkspaceMember


class WorkspaceRepository:
    @staticmethod
    async def create(
        db: AsyncSession, *, name: str, industry: Optional[str] = None
    ) -> Workspace:
        db_obj = Workspace(name=name, industry=industry)
        db.add(db_obj)
        await db.flush()
        return db_obj

    @staticmethod
    async def get(db: AsyncSession, workspace_id: UUID) -> Optional[Workspace]:
        result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
        return result.scalars().first()

    @staticmethod
    async def update(
        db: AsyncSession, *, db_obj: Workspace, obj_in: Dict[str, Any]
    ) -> Workspace:
        for field in obj_in:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_in[field])
        db.add(db_obj)
        await db.flush()
        return db_obj

    @staticmethod
    async def get_stats(db: AsyncSession, workspace_id: UUID) -> Dict[str, int]:
        # Count members in this workspace via workspace_members
        member_count_result = await db.execute(
            select(func.count(WorkspaceMember.id)).where(
                WorkspaceMember.workspace_id == workspace_id
            )
        )
        members_count = member_count_result.scalar() or 0

        return {
            "users_count": members_count,
            "customers_count": 0,
            "conversations_count": 0,
            "tickets_count": 0,
            "documents_count": 0,
        }

    @staticmethod
    async def delete(db: AsyncSession, workspace_id: UUID) -> bool:
        workspace = await WorkspaceRepository.get(db, workspace_id)
        if workspace:
            await db.delete(workspace)
            await db.flush()
            return True
        return False
