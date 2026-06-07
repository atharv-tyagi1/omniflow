import asyncio
import uuid
from backend.app.core.database import engine, Base
from backend.app.models.user import User
from backend.app.models.workspace import Workspace
from backend.app.models.workspace_member import WorkspaceMember
from backend.app.core.security import create_access_token

async def setup_test_user():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        user_id = uuid.uuid4()
        workspace_id = uuid.uuid4()
        
        user = User(
            id=user_id,
            email="test_token@example.com",
            full_name="Test Token",
            hashed_password="fake",
            status="active"
        )
        session.add(user)
        
        workspace = Workspace(
            id=workspace_id,
            name="Test Workspace",
            slug="test-workspace",
            created_by=user_id
        )
        session.add(workspace)
        
        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user_id,
            role="owner"
        )
        session.add(member)
        
        await session.commit()
        
        token = create_access_token(
            subject=str(user_id),
            extra_claims={"workspace_id": str(workspace_id)}
        )
        print(token)

if __name__ == "__main__":
    asyncio.run(setup_test_user())
