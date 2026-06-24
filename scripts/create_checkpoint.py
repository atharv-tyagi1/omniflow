import asyncio
from sqlalchemy import text
from backend.app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        try:
            # Create backups
            await db.execute(text("DROP TABLE IF EXISTS documents_backup_20_6_5;"))
            await db.execute(text("CREATE TABLE documents_backup_20_6_5 AS SELECT * FROM documents;"))
            
            await db.execute(text("DROP TABLE IF EXISTS document_chunks_backup_20_6_5;"))
            await db.execute(text("CREATE TABLE document_chunks_backup_20_6_5 AS SELECT * FROM document_chunks;"))
            
            await db.commit()
            print("Successfully created restore point checkpoint tables (documents_backup_20_6_5, document_chunks_backup_20_6_5)")
        except Exception as e:
            print(f"Error: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(main())
