import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_workspace_isolation_knowledge_search(
    authorized_client: AsyncClient,
    another_authorized_client: AsyncClient,
    workspace_a,
    workspace_b
):
    """
    Test that uploading a document and searching is isolated to the specific workspace.
    """
    # 1. Start document processing in Workspace A
    response_a = await authorized_client.post(
        "/api/v1/knowledge/documents",
        json={"name": "Company Handbook", "file_type": "pdf", "file_url": "https://example.com/handbook.pdf"},
        headers={"X-Workspace-ID": str(workspace_a.id)}
    )
    assert response_a.status_code == 200
    doc_id = response_a.json()["data"]["document_id"]

    # 2. Try to fetch the document from Workspace B (Should fail)
    response_b_get = await another_authorized_client.get(
        f"/api/v1/knowledge/documents/{doc_id}",
        headers={"X-Workspace-ID": str(workspace_b.id)}
    )
    assert response_b_get.status_code in [403, 404]

    # 3. Try to search from Workspace B
    response_b_search = await another_authorized_client.post(
        "/api/v1/knowledge/search",
        json={"query": "handbook", "limit": 5},
        headers={"X-Workspace-ID": str(workspace_b.id)}
    )
    assert response_b_search.status_code == 200
    
    # We should not find any sources from Workspace A
    sources = response_b_search.json()["data"]["sources"]
    assert len(sources) == 0

@pytest.mark.asyncio
async def test_document_deletion(
    authorized_client: AsyncClient,
    workspace_a
):
    """
    Test that a document can be deleted.
    """
    # 1. Create doc
    response = await authorized_client.post(
        "/api/v1/knowledge/documents",
        json={"name": "Temp Doc", "file_type": "txt", "file_url": "https://example.com/temp.txt"},
        headers={"X-Workspace-ID": str(workspace_a.id)}
    )
    doc_id = response.json()["data"]["document_id"]

    # 2. Delete doc
    del_response = await authorized_client.delete(
        f"/api/v1/knowledge/documents/{doc_id}",
        headers={"X-Workspace-ID": str(workspace_a.id)}
    )
    assert del_response.status_code == 200

    # 3. Fetch again (should be 404)
    get_response = await authorized_client.get(
        f"/api/v1/knowledge/documents/{doc_id}",
        headers={"X-Workspace-ID": str(workspace_a.id)}
    )
    assert get_response.status_code == 404
