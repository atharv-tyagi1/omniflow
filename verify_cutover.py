import asyncio
import os
from sqlalchemy import text
from backend.app.core.database import AsyncSessionLocal, engine
from backend.app.core.config import settings

async def main():
    print("=== POSTGRESQL CUTOVER VERIFICATION ===")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    print(f"SYNC_DATABASE_URL: {settings.SYNC_DATABASE_URL}")
    print(f"Engine dialect: {engine.dialect.name}")
    
    if engine.dialect.name != "postgresql":
        print("FAIL: Dialect is not postgresql")
        return

    async with AsyncSessionLocal() as db:
        try:
            # Check pgvector extension
            res = await db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';"))
            ext = res.scalar()
            if ext == 'vector':
                print("PASS: pgvector extension exists")
            else:
                print("FAIL: pgvector extension missing")

            # Check table count
            res = await db.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"))
            table_count = res.scalar()
            print(f"Table count in public schema: {table_count}")

            # Get some table names to verify
            res = await db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 5;"))
            tables = [row[0] for row in res.fetchall()]
            print(f"Some tables: {tables}")

            print("PASS: Database Connection and State OK")
        except Exception as e:
            print(f"FAIL: Database error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
