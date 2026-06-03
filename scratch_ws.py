import asyncio
from sqlalchemy import select
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.workspace import Workspace

async def get_ws():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Workspace))
        ws = result.scalars().first()
        if not ws:
            print("Creating dummy workspace")
            ws = Workspace(name="Test Workspace")
            db.add(ws)
            await db.commit()
            await db.refresh(ws)
        print(f"WORKSPACE_ID={ws.id}")

if __name__ == "__main__":
    asyncio.run(get_ws())
