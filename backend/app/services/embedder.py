from typing import List
from openai import AsyncOpenAI, APIError, RateLimitError, AuthenticationError
from backend.app.core.config import settings
from backend.app.core.errors import EmbeddingServiceError
from backend.app.core.logging import logger


class EmbeddingService:
    def __init__(self):
        self.model = settings.OPENAI_EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION

    def _get_client(self) -> AsyncOpenAI:
        api_key = settings.effective_api_key
        if not api_key:
            raise EmbeddingServiceError("No AI API key (GEMINI_API_KEY or OPENAI_API_KEY) is configured on the server.")
        
        kwargs = {"api_key": api_key}
        if settings.OPENAI_BASE_URL:
            kwargs["base_url"] = settings.OPENAI_BASE_URL
        return AsyncOpenAI(**kwargs)

    async def generate_embeddings(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        """
        Generates vector embeddings for a list of texts in batches using OpenAI text-embedding-3-small.
        Validates the output dimensions.
        """
        if not texts:
            return []

        client = self._get_client()
        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                create_kwargs = {"model": self.model, "input": batch}
                if self.dimension:
                    create_kwargs["dimensions"] = self.dimension

                response = await client.embeddings.create(**create_kwargs)
                # Sort by index to maintain ordering guarantees
                sorted_data = sorted(response.data, key=lambda x: x.index)
                for item in sorted_data:
                    emb = item.embedding
                    if len(emb) != self.dimension:
                        logger.error(
                            "Embedding dimension mismatch: expected %d, got %d",
                            self.dimension,
                            len(emb),
                        )
                        raise EmbeddingServiceError(
                            f"Embedding dimension mismatch: expected {self.dimension}, got {len(emb)}"
                        )
                    all_embeddings.append(emb)

            except AuthenticationError as e:
                logger.error("OpenAI authentication error during embedding generation: %s", e)
                raise EmbeddingServiceError("Authentication failed with OpenAI embedding provider.")
            except RateLimitError as e:
                logger.warning("OpenAI rate limit exceeded during embedding generation: %s", e)
                raise EmbeddingServiceError("OpenAI embedding rate limit exceeded. Please retry shortly.")
            except APIError as e:
                logger.error("OpenAI API error during embedding generation: %s", e)
                raise EmbeddingServiceError(f"OpenAI embedding service error: {e.message or 'Request failed'}")
            except Exception as e:
                if isinstance(e, EmbeddingServiceError):
                    raise
                logger.error("Unexpected error in embedding generation: %s", e)
                raise EmbeddingServiceError(f"Failed to generate embeddings: {str(e)}")

        return all_embeddings

    async def generate_single_embedding(self, text: str) -> List[float]:
        embeddings = await self.generate_embeddings([text])
        if not embeddings:
            raise EmbeddingServiceError("Failed to generate embedding for input.")
        return embeddings[0]


embedding_service = EmbeddingService()
