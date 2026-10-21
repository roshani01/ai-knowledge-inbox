import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.core.errors import EmbeddingServiceError
from backend.app.services.embedder import EmbeddingService


@pytest.mark.asyncio
async def test_embedder_dimension_validation():
    embedder = EmbeddingService()

    # Mock response with wrong dimension (e.g., 512 instead of 1536)
    mock_data_wrong_dim = MagicMock()
    mock_data_wrong_dim.index = 0
    mock_data_wrong_dim.embedding = [0.1] * 512

    mock_client = AsyncMock()
    mock_client.embeddings.create.return_value = MagicMock(data=[mock_data_wrong_dim])

    with patch.object(embedder, "_get_client", return_value=mock_client):
        with pytest.raises(EmbeddingServiceError) as exc_info:
            await embedder.generate_embeddings(["Sample text"])
        assert "dimension mismatch" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_embedder_handles_empty_input():
    embedder = EmbeddingService()
    result = await embedder.generate_embeddings([])
    assert result == []
