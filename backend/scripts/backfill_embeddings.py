import asyncio
import argparse
import json
import os
import sys
import logging
from pathlib import Path

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from backend.app.core.database import AsyncSessionLocal
from backend.app.models.document import Document
from backend.app.services.knowledge_service import KnowledgeService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CHECKPOINT_FILE = "embedding_backfill_checkpoint.json"

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"processed": [], "failed": []}

def save_checkpoint(data):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(data, f)

async def get_documents_to_process(session: AsyncSession, retry_failed: bool):
    # Fetch documents that are missing correct embedding metadata
    conditions = [
        Document.embedding_dim != 768,
        Document.embedding_model.is_(None)
    ]
    if retry_failed:
        conditions.append(Document.status == "failed")
        
    stmt = select(Document).where(or_(*conditions))
    result = await session.execute(stmt)
    return result.scalars().all()

async def main():
    parser = argparse.ArgumentParser(description="Backfill document embeddings to 768 dimensions.")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint file.")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of documents to process in a batch.")
    parser.add_argument("--retry-failed", action="store_true", help="Include documents with 'failed' status.")
    args = parser.parse_args()

    checkpoint = {"processed": [], "failed": []}
    if args.resume:
        checkpoint = load_checkpoint()
        logger.info(f"Loaded checkpoint. Processed: {len(checkpoint['processed'])}, Failed: {len(checkpoint['failed'])}")

    async with AsyncSessionLocal() as session:
        docs = await get_documents_to_process(session, args.retry_failed)
        
    to_process = [d for d in docs if str(d.id) not in checkpoint["processed"]]
    logger.info(f"Found {len(docs)} total documents needing backfill. {len(to_process)} remaining after checkpoint filter.")

    success_count = 0
    failure_count = 0

    for i in range(0, len(to_process), args.batch_size):
        batch = to_process[i:i+args.batch_size]
        logger.info(f"Processing batch {i // args.batch_size + 1}...")
        
        for doc in batch:
            try:
                # Call existing idempotent task
                await KnowledgeService.process_document_task(
                    document_id=doc.id,
                    workspace_id=doc.workspace_id,
                    file_url=doc.file_url,
                    file_type=doc.file_type
                )
                
                # Verify it succeeded
                async with AsyncSessionLocal() as session:
                    verify_result = await session.execute(select(Document).where(Document.id == doc.id))
                    verified_doc = verify_result.scalars().first()
                    
                    if verified_doc.status == "ready" and verified_doc.embedding_dim == 768:
                        checkpoint["processed"].append(str(doc.id))
                        success_count += 1
                        logger.info(f"Successfully backfilled doc: {doc.id}")
                    else:
                        raise ValueError(f"Document {doc.id} verification failed after processing.")
                        
            except Exception as e:
                logger.error(f"Failed to process doc {doc.id}: {e}")
                checkpoint["failed"].append(str(doc.id))
                failure_count += 1
                
        # Save checkpoint after each batch
        save_checkpoint(checkpoint)
        
    logger.info("=== Backfill Summary ===")
    logger.info(f"Total processed successfully in this run: {success_count}")
    logger.info(f"Total failed in this run: {failure_count}")
    logger.info(f"Total historical processed: {len(checkpoint['processed'])}")
    logger.info(f"Total historical failed: {len(checkpoint['failed'])}")

if __name__ == "__main__":
    asyncio.run(main())
