import pytest
from httpx import AsyncClient
import uuid
from backend.app.core.database import AsyncSessionLocal
from backend.app.services.knowledge_service import KnowledgeService
from backend.app.models.document import Document
from backend.app.models.document_chunk import DocumentChunk
from sqlalchemy import select, text

@pytest.mark.asyncio
async def test_background_processor_success(db):
    # Setup test document
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    
    from backend.app.models.user import User
    from backend.app.models.workspace import Workspace
    user = User(id=user_id, email="user@test.com", full_name="Test User", password_hash="hash", status="active")
    workspace = Workspace(id=workspace_id, name="Test Workspace", plan="free", status="active")
    
    test_file_path = f"test_{doc_id}.txt"
    with open(test_file_path, "wb") as f:
        f.write(b"This is a real integration test text.")
        
    doc = Document(id=doc_id, workspace_id=workspace_id, name="Test Doc", file_type="text/plain", file_url=f"file://{test_file_path}", status="pending", uploaded_by=user_id)
    db.add(user)
    db.add(workspace)
    db.add(doc)
    await db.commit()
    
    # Execute actual background task
    from unittest.mock import patch
    from backend.tests.conftest import TestingSessionLocal
    with patch("backend.app.services.knowledge_service.AsyncSessionLocal", new=TestingSessionLocal):
        await KnowledgeService.process_document_task(doc_id, workspace_id, f"file://{test_file_path}", "text/plain")
        
        # Verify integration
        async with TestingSessionLocal() as db:
            doc_result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = doc_result.scalars().first()
            assert doc is not None
            assert doc.status == "ready"
            assert doc.embedding_model == "gemini-embedding-2-768"
            
            chunks = await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc_id))
            assert len(chunks.scalars().all()) > 0
    
    import os
    os.remove(test_file_path)

@pytest.mark.asyncio
async def test_background_processor_rollback_on_failure(db):
    # Setup test document
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    
    from backend.app.models.user import User
    from backend.app.models.workspace import Workspace
    user = User(id=user_id, email="user2@test.com", full_name="Test User 2", password_hash="hash", status="active")
    workspace = Workspace(id=workspace_id, name="Test Workspace 2", plan="free", status="active")
    doc = Document(id=doc_id, workspace_id=workspace_id, name="Fail Doc", file_type="text/plain", file_url="file://nonexistent.txt", status="pending", uploaded_by=user_id)
    db.add(user)
    db.add(workspace)
    db.add(doc)
    await db.commit()
    
    # Execute actual background task (will fail)
    from unittest.mock import patch
    from backend.tests.conftest import TestingSessionLocal
    with patch("backend.app.services.knowledge_service.AsyncSessionLocal", new=TestingSessionLocal):
        await KnowledgeService.process_document_task(doc_id, workspace_id, "file://nonexistent.txt", "text/plain")
        
        # Verify rollback behavior: status becomes 'failed', no chunks inserted
        async with TestingSessionLocal() as db:
            doc_result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = doc_result.scalars().first()
            assert doc is not None
            assert doc.status == "failed"
            
            chunks = await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc_id))
            assert len(chunks.scalars().all()) == 0
