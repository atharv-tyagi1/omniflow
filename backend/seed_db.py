import asyncio
from uuid import UUID
from datetime import datetime, timezone

from backend.app.core.database import engine, Base
from backend.app.models.user import User
from backend.app.models.workspace import Workspace, WorkspaceUser
from backend.app.core.security import get_password_hash

async def seed():
    async with engine.begin() as conn:
        from sqlalchemy import text
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.run_sync(Base.metadata.create_all)

    # We need a session to insert data
    from backend.app.core.database import SessionLocal
    async with SessionLocal() as session:
        # Create a workspace
        workspace_id = UUID("00000000-0000-0000-0000-000000000000")
        ws = Workspace(
            id=workspace_id,
            name="OmniFlow Production Workspace",
            tier="pro",
            status="active"
        )
        session.add(ws)

        # Create a user
        user_id = UUID("11111111-1111-1111-1111-111111111111")
        user = User(
            id=user_id,
            email="admin@omniflow.com",
            hashed_password=get_password_hash("password"),
            full_name="OmniFlow Admin",
            status="active"
        )
        session.add(user)
        
        # Link user to workspace as owner
        ws_user = WorkspaceUser(
            workspace_id=workspace_id,
            user_id=user_id,
            role="owner"
        )
        session.add(ws_user)

        # Create some other workspace members
        member_id = UUID("22222222-2222-2222-2222-222222222222")
        member = User(
            id=member_id,
            email="member@omniflow.com",
            hashed_password=get_password_hash("password"),
            full_name="OmniFlow Member",
            status="active"
        )
        session.add(member)
        ws_member = WorkspaceUser(
            workspace_id=workspace_id,
            user_id=member_id,
            role="member"
        )
        session.add(ws_member)

        await session.commit()
        print("Database seeded successfully with workspace, user, and relations.")

if __name__ == "__main__":
    asyncio.run(seed())
