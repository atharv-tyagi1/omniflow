from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List, Optional

from backend.app.models.workspace_member import WorkspaceMember


class WorkspaceMemberRepository:
    @staticmethod
    async def create(
        db: AsyncSession, workspace_id: UUID, user_id: UUID, role: str = "member"
    ) -> WorkspaceMember:
        db_member = WorkspaceMember(
            workspace_id=workspace_id, user_id=user_id, role=role
        )
        db.add(db_member)
        await db.commit()
        await db.refresh(db_member)
        return db_member

    @staticmethod
    async def get_by_user_and_workspace(
        db: AsyncSession, user_id: UUID, workspace_id: UUID
    ) -> Optional[WorkspaceMember]:
        result = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.workspace_id == workspace_id,
            )
        )
        return result.scalars().first()

    @staticmethod
    async def get_workspaces_for_user(db: AsyncSession, user_id: UUID) -> List[WorkspaceMember]:
        result = await db.execute(
            select(WorkspaceMember).where(WorkspaceMember.user_id == user_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_members_for_workspace(db: AsyncSession, workspace_id: UUID) -> List[WorkspaceMember]:
        # Using joinedload to fetch User info would be better if needed, 
        # but selectinload is configured on the relationship.
        result = await db.execute(
            select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
        )
        return list(result.scalars().all())
