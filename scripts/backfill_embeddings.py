import asyncio
import argparse
from sqlalchemy import text, select
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.document import Document
from backend.app.services.knowledge_service import KnowledgeService
import sys

async def main(dry_run=False):
    print("=== EMBEDDING BACKFILL START ===")
    
    async with AsyncSessionLocal() as db:
        # Find all documents that need re-embedding
        # i.e., embedding_model is not 'gemini-embedding-2-768'
        stmt = text("SELECT id, workspace_id, file_url, file_type FROM documents WHERE embedding_model IS NULL OR embedding_model != 'gemini-embedding-2-768'")
        res = await db.execute(stmt)
        docs = res.fetchall()
        
        print(f"Found {len(docs)} documents needing embedding backfill.")
        
        if dry_run:
            print("DRY RUN: Exiting without making changes.")
            sys.exit(0)
            
        for doc in docs:
            doc_id, workspace_id, file_url, file_type = doc
            print(f"Backfilling Document: {doc_id}")
            
            # Delete old chunks for this document to make it idempotent
            await db.execute(text("DELETE FROM document_chunks WHERE document_id = :doc_id"), {"doc_id": doc_id})
            await db.commit()
            
            # Now run the process_document_task which fetches, chunks, embeds, inserts, and updates metadata
            # We call it directly
            try:
                await KnowledgeService.process_document_task(doc_id, workspace_id, file_url, file_type)
                print(f"Successfully backfilled document {doc_id}")
            except Exception as e:
                print(f"Failed to backfill document {doc_id}: {e}")
                
        # Final Verification
        print("\n=== VERIFICATION ===")
        res = await db.execute(text("SELECT embedding_model, count(*) FROM documents GROUP BY embedding_model"))
        print("Documents by embedding_model:", res.fetchall())
        
        res = await db.execute(text("SELECT count(*) FROM document_chunks"))
        chunks = res.scalar()
        print(f"Total vector chunks active: {chunks}")
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill document embeddings")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done without doing it")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
