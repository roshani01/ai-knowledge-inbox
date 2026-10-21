from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest
from httpx import AsyncClient
from backend.app.core.errors import EmbeddingServiceError


@pytest.mark.asyncio
async def test_ingest_valid_note(client: AsyncClient, mock_openai_embedder):
    payload = {
        "source_type": "note",
        "title": "Architecture Decisions",
        "content": "We chose PostgreSQL with pgvector for unified relational and vector data storage.",
    }
    response = await client.post("/ingest", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Architecture Decisions"
    assert data["source_type"] == "note"
    assert data["indexing_status"] == "indexed"
    assert data["chunk_count"] >= 1
    assert "id" in data


@pytest.mark.asyncio
async def test_ingest_empty_note_rejected(client: AsyncClient):
    # Empty title
    response = await client.post(
        "/ingest",
        json={"source_type": "note", "title": "   ", "content": "Some valid content"},
    )
    assert response.status_code == 422

    # Empty content
    response = await client.post(
        "/ingest",
        json={"source_type": "note", "title": "Valid Title", "content": "   \n\t  "},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ingest_unsafe_url_ssrf_blocked(client: AsyncClient):
    response = await client.post(
        "/ingest",
        json={"source_type": "url", "url": "http://127.0.0.1:8000/internal"},
    )
    assert response.status_code == 400
    assert "restricted" in response.json()["detail"].lower() or "blocked" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ingest_url_success(client: AsyncClient, mock_openai_embedder):
    fake_html = """
    <html>
      <head><title>FastAPI Documentation</title></head>
      <body><main><h1>High Performance Web Framework</h1><p>FastAPI is very fast and modern.</p></main></body>
    </html>
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.is_redirect = False
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.content = fake_html.encode("utf-8")
    mock_resp.text = fake_html

    with patch("backend.app.services.url_extractor.validate_url_for_ssrf"), patch(
        "httpx.AsyncClient.get", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = mock_resp
        response = await client.post(
            "/ingest",
            json={"source_type": "url", "url": "https://example.com/docs"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "FastAPI Documentation"
        assert data["source_type"] == "url"
        assert data["indexing_status"] == "indexed"
        assert data["chunk_count"] >= 1


@pytest.mark.asyncio
async def test_ingest_url_timeout_handled(client: AsyncClient):
    with patch("backend.app.services.url_extractor.validate_url_for_ssrf"), patch(
        "httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Timed out")
    ):
        response = await client.post(
            "/ingest",
            json={"source_type": "url", "url": "https://example.com/timeout-test"},
        )
        assert response.status_code == 422
        assert "timed out" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ingest_embedding_failure_marks_item_failed(client: AsyncClient):
    with patch(
        "backend.app.services.embedder.embedding_service.generate_embeddings",
        side_effect=EmbeddingServiceError("OpenAI embedding rate limit exceeded."),
    ):
        payload = {
            "source_type": "note",
            "title": "Rate Limit Note",
            "content": "This note should fail gracefully when embedding fails.",
        }
        response = await client.post("/ingest", json=payload)
        # Should return 502 Bad Gateway
        assert response.status_code == 502
        assert "rate limit" in response.json()["detail"].lower()

        # Check that the item exists in /items with 'failed' status
        items_resp = await client.get("/items")
        assert items_resp.status_code == 200
        items_data = items_resp.json()["items"]
        failed_item = next((i for i in items_data if i["title"] == "Rate Limit Note"), None)
        assert failed_item is not None
        assert failed_item["indexing_status"] == "failed"
        assert "rate limit" in failed_item["error_message"].lower()
