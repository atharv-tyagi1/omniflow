import asyncio
from uuid import UUID
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.models.workspace import Workspace
from backend.app.models.workspace_member import WorkspaceMember
from backend.app.core.security import hash_password
from sqlalchemy import select

async def seed():
    async with AsyncSessionLocal() as session:
        workspace_id = UUID("00000000-0000-0000-0000-000000000000")
        
        # Check if workspace exists
        result = await session.execute(select(Workspace).where(Workspace.id == workspace_id))
        ws = result.scalar_one_or_none()
        if not ws:
            ws = Workspace(
                id=workspace_id,
                name="OmniFlow Production Workspace",
                plan="pro",
                status="active"
            )
            session.add(ws)

        # Check if user exists
        user_id = UUID("11111111-1111-1111-1111-111111111111")
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                id=user_id,
                email="admin@omniflow.com",
                password_hash=hash_password("password"),
                full_name="OmniFlow Admin",
                status="active"
            )
            session.add(user)
        else:
            # ensure password is correct
            user.password_hash = hash_password("password")
        
        # Check workspace user link
        result = await session.execute(
            select(WorkspaceMember)
            .where(WorkspaceMember.workspace_id == workspace_id)
            .where(WorkspaceMember.user_id == user_id)
        )
        ws_user = result.scalar_one_or_none()
        if not ws_user:
            ws_user = WorkspaceMember(
                workspace_id=workspace_id,
                user_id=user_id,
                role="owner"
            )
            session.add(ws_user)

        try:
            await session.commit()
            print("Database seeded successfully with admin user.")
        except Exception as e:
            print("Seed error (might already exist):", e)

if __name__ == "__main__":
    asyncio.run(seed())
