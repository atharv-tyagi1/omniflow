"""Tests for document knowledge service and workspace isolation."""

import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient


# Patch out the background processing task that tries to download files
# and connect to production Postgres. We only test the CRUD layer here.
PATCH_TARGET = "backend.app.controllers.document_controller.KnowledgeService.process_document_task"


@pytest.mark.asyncio
@patch(PATCH_TARGET, new_callable=AsyncMock)
async def test_workspace_isolation_knowledge_search(
    mock_process, async_client: AsyncClient, auth_a, auth_b
):
    """
    A document uploaded to Workspace A must not surface in Workspace B searches.
    """
    # 1. Upload a document in Workspace A
    response_a = await async_client.post(
        "/api/v1/knowledge/documents",
        json={
            "name": "Company Handbook",
            "file_type": "pdf",
            "file_url": "https://example.com/handbook.pdf",
        },
        headers={
            "Authorization": f"Bearer {auth_a.token}",
            "X-Workspace-ID": auth_a.workspace_id,
        },
    )
    assert response_a.status_code == 200, response_a.text
    doc_id = response_a.json()["data"]["document_id"]

    # 2. Fetch from Workspace B — must fail
    response_b_get = await async_client.get(
        f"/api/v1/knowledge/documents/{doc_id}",
        headers={
            "Authorization": f"Bearer {auth_b.token}",
            "X-Workspace-ID": auth_b.workspace_id,
        },
    )
    assert response_b_get.status_code in [403, 404]


@pytest.mark.asyncio
@patch(PATCH_TARGET, new_callable=AsyncMock)
async def test_document_deletion(mock_process, async_client: AsyncClient, auth_a):
    """
    Upload → Delete → Fetch should return 404.
    """
    # 1. Create doc
    response = await async_client.post(
        "/api/v1/knowledge/documents",
        json={
            "name": "Temp Doc",
            "file_type": "txt",
            "file_url": "https://example.com/temp.txt",
        },
        headers={
            "Authorization": f"Bearer {auth_a.token}",
            "X-Workspace-ID": auth_a.workspace_id,
        },
    )
    assert response.status_code == 200, response.text
    doc_id = response.json()["data"]["document_id"]

    # 2. Delete doc
    del_response = await async_client.delete(
        f"/api/v1/knowledge/documents/{doc_id}",
        headers={
            "Authorization": f"Bearer {auth_a.token}",
            "X-Workspace-ID": auth_a.workspace_id,
        },
    )
    assert del_response.status_code == 200

    # 3. Fetch again (should be 404)
    get_response = await async_client.get(
        f"/api/v1/knowledge/documents/{doc_id}",
        headers={
            "Authorization": f"Bearer {auth_a.token}",
            "X-Workspace-ID": auth_a.workspace_id,
        },
    )
    assert get_response.status_code == 404
