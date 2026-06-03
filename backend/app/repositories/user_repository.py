from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import Optional, List, Dict, Any
from backend.app.models.user import User

class UserRepository:
    @staticmethod
    async def create(
        db: AsyncSession, 
        *, 
        email: str, 
        full_name: str, 
        password_hash: str, 
        role: str = "member", 
        workspace_id: UUID
    ) -> User:
        db_obj = User(
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            role=role,
            workspace_id=workspace_id
        )
        db.add(db_obj)
        await db.flush()
        return db_obj

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    @staticmethod
    async def list_by_workspace(db: AsyncSession, workspace_id: UUID) -> List[User]:
        result = await db.execute(select(User).where(User.workspace_id == workspace_id))
        return result.scalars().all()

    @staticmethod
    async def update(db: AsyncSession, *, db_obj: User, obj_in: Dict[str, Any]) -> User:
        for field in obj_in:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_in[field])
        db.add(db_obj)
        await db.flush()
        return db_obj

    @staticmethod
    async def delete(db: AsyncSession, user_id: UUID) -> bool:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if user:
            await db.delete(user)
            await db.flush()
            return True
        return False
