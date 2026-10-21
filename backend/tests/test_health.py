import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "timestamp" in data
    assert data["embedding_model"] in ("gemini-embedding-001", "text-embedding-004", "text-embedding-3-small")
    assert data["embedding_dimension"] in (768, 1536)
    assert data["chat_model"] in ("gemini-3.5-flash", "gemini-1.5-flash", "gpt-4o-mini")
