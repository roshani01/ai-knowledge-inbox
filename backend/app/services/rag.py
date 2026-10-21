from typing import List, Tuple
from openai import AsyncOpenAI, APIError, RateLimitError, AuthenticationError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.errors import LLMServiceError
from backend.app.core.logging import logger
from backend.app.models.knowledge import KnowledgeChunk, KnowledgeItem
from backend.app.schemas.query import Citation, QueryResponse
from backend.app.services.embedder import embedding_service
from backend.app.services.vector_search import search_similar_chunks


class RAGService:
    def __init__(self):
        self.chat_model = settings.OPENAI_CHAT_MODEL

    def _get_client(self) -> AsyncOpenAI:
        api_key = settings.effective_api_key
        if not api_key:
            raise LLMServiceError("No AI API key (GEMINI_API_KEY or OPENAI_API_KEY) is configured on the server.")
        
        kwargs = {"api_key": api_key}
        if settings.OPENAI_BASE_URL:
            kwargs["base_url"] = settings.OPENAI_BASE_URL
        return AsyncOpenAI(**kwargs)

    def _format_context(
        self, retrieved: List[Tuple[KnowledgeChunk, KnowledgeItem, float]]
    ) -> str:
        context_parts = []
        for idx, (chunk, item, score) in enumerate(retrieved, start=1):
            source_info = f"[Source {idx}] Title: {item.title} (Type: {item.source_type}"
            if item.original_url:
                source_info += f", URL: {item.original_url}"
            source_info += f", Relevance: {score:.2f})"
            context_parts.append(f"{source_info}\nContent:\n{chunk.content}")
        return "\n\n---\n\n".join(context_parts)

    def _build_citations(
        self, retrieved: List[Tuple[KnowledgeChunk, KnowledgeItem, float]]
    ) -> List[Citation]:
        citations = []
        for chunk, item, score in retrieved:
            # Create a clean snippet
            snippet = chunk.content.strip()
            if len(snippet) > 280:
                snippet = snippet[:280].rstrip() + "..."

            citations.append(
                Citation(
                    chunk_id=chunk.id,
                    item_id=item.id,
                    title=item.title,
                    source_type=item.source_type,
                    url=item.original_url,
                    snippet=snippet,
                    similarity_score=round(score, 3),
                )
            )
        return citations

    async def answer_question(
        self, question: str, session: AsyncSession
    ) -> QueryResponse:
        """
        Executes end-to-end RAG:
        1. Embeds question.
        2. Retrieves relevant chunks via pgvector cosine distance.
        3. Prompts LLM with strict grounding instructions.
        4. Returns answer and verifiable citations.
        """
        logger.info("Processing RAG query: '%s'", question[:80])

        # Step 1: Embed question
        query_embedding = await embedding_service.generate_single_embedding(question)

        # Step 2: Retrieve candidate chunks
        retrieved = await search_similar_chunks(
            session=session,
            query_embedding=query_embedding,
            limit=settings.TOP_K_RETRIEVAL,
        )

        if not retrieved:
            logger.info("No indexed knowledge items found for query.")
            return QueryResponse(
                question=question,
                answer="Your saved knowledge inbox is either empty or does not contain any relevant information to answer this question.",
                citations=[],
                has_sufficient_context=False,
            )

        # Step 3: Construct prompt
        context_text = self._format_context(retrieved)
        system_prompt = (
            "You are an AI Knowledge Assistant grounded strictly in the user's saved knowledge inbox.\n"
            "Instructions:\n"
            "1. Answer the user's question using ONLY the facts directly stated in the provided Context.\n"
            "2. If the context does not contain enough information to answer the question, clearly state: "
            "'The saved knowledge does not provide enough information to answer this question.'\n"
            "3. Do NOT make assumptions, guess, or use external knowledge not present in the Context.\n"
            "4. Keep the answer clear, helpful, and concise.\n"
            "5. Never invent or falsify URLs, titles, or source citations."
        )

        user_prompt = f"Context:\n{context_text}\n\nQuestion: {question}\n\nAnswer:"

        client = self._get_client()

        models_to_try = [self.chat_model]
        if "gemini" in self.chat_model.lower():
            for alt in ["gemini-3.8-flash", "gemini-flash-latest"]:
                if alt not in models_to_try:
                    models_to_try.append(alt)

        response = None
        last_exc = None

        for model_candidate in models_to_try:
            try:
                response = await client.chat.completions.create(
                    model=model_candidate,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.1,
                )
                break
            except Exception as e:
                last_exc = e
                logger.warning("Model %s request failed: %s", model_candidate, e)

        if not response:
            if isinstance(last_exc, LLMServiceError):
                raise last_exc
            raise LLMServiceError(f"Failed to generate answer: {str(last_exc) if last_exc else 'No response from model'}")

        try:
            answer_content = response.choices[0].message.content or ""
            answer = answer_content.strip()

        except AuthenticationError as e:
            logger.error("OpenAI authentication error: %s", e)
            raise LLMServiceError("Authentication failed with OpenAI service.")
        except RateLimitError as e:
            logger.warning("OpenAI rate limit: %s", e)
            raise LLMServiceError("OpenAI rate limit reached. Please retry in a moment.")
        except APIError as e:
            logger.error("OpenAI API error: %s", e)
            raise LLMServiceError(f"OpenAI service error: {e.message or 'Request failed'}")
        except Exception as e:
            logger.error("Unexpected error in chat completion: %s", e)
            raise LLMServiceError(f"Failed to generate answer: {str(e)}")

        # Step 4: Check if context was sufficient
        insufficient_phrases = [
            "does not provide enough information",
            "not enough information",
            "do not contain enough information",
            "no information provided",
            "cannot be answered based on the provided context",
        ]
        has_sufficient_context = not any(phrase in answer.lower() for phrase in insufficient_phrases)

        citations = self._build_citations(retrieved)

        return QueryResponse(
            question=question,
            answer=answer,
            citations=citations,
            has_sufficient_context=has_sufficient_context,
        )


rag_service = RAGService()
