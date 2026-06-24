import asyncio
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import select
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.document import Document

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Document))
        docs = result.scalars().all()
        print(f"Total docs: {len(docs)}")

asyncio.run(main())
