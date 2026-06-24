import asyncio
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import text
from backend.app.core.database import AsyncSessionLocal
import json

async def main():
    async with AsyncSessionLocal() as session:
        # 1. Check pgvector extension
        ext_res = await session.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'"))
        ext = ext_res.fetchone()
        print(f"Vector Extension: {ext}")
        
        # 2. Check indexes on document_chunks table
        idx_res = await session.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'document_chunks'
        """))
        indexes = idx_res.fetchall()
        for idx in indexes:
            print(f"Index: {idx.indexname} -> {idx.indexdef}")
            
        # 3. Check query plan for vector search
        # Mock 768-dimensional vector
        mock_vector = "[" + ",".join(["0.1"] * 768) + "]"
        workspace_id = "00000000-0000-0000-0000-000000000000"
        
        # Explain analyze
        await session.execute(text("SET enable_seqscan = off;"))
        await session.execute(text("SET enable_sort = off;"))
        
        explain_q = text(f"""
            EXPLAIN ANALYZE
            SELECT document_chunks.id
            FROM document_chunks
            JOIN documents ON documents.id = document_chunks.document_id
            WHERE documents.workspace_id = '{workspace_id}'
            ORDER BY document_chunks.embedding <=> '{mock_vector}'
            LIMIT 5
        """)
        
        try:
            plan_res = await session.execute(explain_q)
            plan = plan_res.fetchall()
            print("\nQuery Plan:")
            for p in plan:
                print(p[0])
        except Exception as e:
            print(f"Query plan error: {e}")

asyncio.run(main())
