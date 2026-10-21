from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient
from backend.app.core.errors import LLMServiceError


@pytest.mark.asyncio
async def test_query_empty_question_rejected(client: AsyncClient):
    response = await client.post("/query", json={"question": "   "})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_query_empty_inbox(client: AsyncClient, mock_openai_embedder):
    response = await client.post("/query", json={"question": "What is our company onboarding policy?"})
    assert response.status_code == 200
    data = response.json()
    assert data["has_sufficient_context"] is False
    assert data["citations"] == []
    assert "either empty or does not contain" in data["answer"].lower()


@pytest.mark.asyncio
async def test_query_grounded_answer_with_citations(client: AsyncClient, mock_openai_embedder):
    # Ingest a note first
    await client.post(
        "/ingest",
        json={
            "source_type": "note",
            "title": "Employee Handbook",
            "content": "Onboarding takes 3 days and requires completing the security checklist and laptop setup.",
        },
    )

    # Mock chat completion
    mock_choice = MagicMock()
    mock_choice.message.content = "Onboarding takes 3 days and requires completing the security checklist and laptop setup."
    mock_response = MagicMock(choices=[mock_choice])

    from backend.app.services.rag import rag_service

    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch.object(rag_service, "_get_client", return_value=mock_client):
        response = await client.post(
            "/query",
            json={"question": "How long does onboarding take?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "3 days" in data["answer"]
        assert data["has_sufficient_context"] is True
        assert len(data["citations"]) > 0

        first_citation = data["citations"][0]
        assert "chunk_id" in first_citation
        assert "item_id" in first_citation
        assert first_citation["title"] == "Employee Handbook"
        assert first_citation["source_type"] == "note"
        assert "snippet" in first_citation
        assert "similarity_score" in first_citation


@pytest.mark.asyncio
async def test_query_llm_failure_handling(client: AsyncClient, mock_openai_embedder):
    # Ingest a note so context exists
    await client.post(
        "/ingest",
        json={
            "source_type": "note",
            "title": "Project Info",
            "content": "Project Antigravity focuses on agentic AI capabilities.",
        },
    )

    from backend.app.services.rag import rag_service

    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = Exception("OpenAI API connection error")

    with patch.object(rag_service, "_get_client", return_value=mock_client):
        response = await client.post(
            "/query",
            json={"question": "What is Project Antigravity?"},
        )
        assert response.status_code == 502
        assert "failed to generate answer" in response.json()["detail"].lower()
