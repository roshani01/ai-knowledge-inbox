from typing import Union
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.errors import AppException, EmbeddingServiceError, UrlFetchError
from backend.app.core.logging import logger
from backend.app.models.knowledge import KnowledgeChunk, KnowledgeItem
from backend.app.schemas.ingest import (
    IngestNoteRequest,
    IngestResponse,
    IngestUrlRequest,
)
from backend.app.services.chunker import chunk_text
from backend.app.services.embedder import embedding_service
from backend.app.services.url_extractor import fetch_and_extract_url


async def ingest_knowledge(
    request: Union[IngestNoteRequest, IngestUrlRequest],
    session: AsyncSession,
) -> IngestResponse:
    """
    Orchestrates the ingestion pipeline:
    1. Extracts text content (from raw note or via SSRF-safe URL extraction).
    2. Persists KnowledgeItem in 'pending' status.
    3. Splits text into semantic chunks.
    4. Generates embeddings in batches.
    5. Saves chunks with vector embeddings and marks item 'indexed'.
    If any downstream embedding or DB failure occurs, the item is marked 'failed'
    with a safe, user-friendly error message.
    """
    source_type = request.source_type
    original_url = None
    title = ""
    content = ""

    # Step 1: Content Extraction
    if source_type == "note":
        title = request.title.strip()
        content = request.content.strip()
        logger.info("Ingesting note: '%s' (%d chars)", title, len(content))
    elif source_type == "url":
        url_target = request.url.strip()
        logger.info("Ingesting URL: %s", url_target)
        extracted = await fetch_and_extract_url(url_target)
        title = extracted.title
        content = extracted.content
        original_url = extracted.url
    else:
        raise AppException("Unsupported source type.", status_code=400)

    # Step 2: Initialize KnowledgeItem record
    item = KnowledgeItem(
        title=title,
        source_type=source_type,
        original_content=content,
        original_url=original_url,
        indexing_status="pending",
    )
    session.add(item)
    await session.flush()  # Obtain item.id

    # Step 3: Chunking
    chunks = chunk_text(content)
    if not chunks:
        item.indexing_status = "failed"
        item.error_message = "No readable text content found to index."
        await session.commit()
        raise AppException("Content was empty or unparseable after processing.", status_code=422)

    logger.info("Generated %d chunks for item %s", len(chunks), item.id)

    # Step 4 & 5: Embeddings & Vector Storage
    try:
        chunk_texts = [c.content for c in chunks]
        embeddings = await embedding_service.generate_embeddings(chunk_texts)

        for chunk_meta, emb in zip(chunks, embeddings):
            chunk_row = KnowledgeChunk(
                item_id=item.id,
                chunk_index=chunk_meta.chunk_index,
                content=chunk_meta.content,
                embedding=emb,
            )
            session.add(chunk_row)

        item.indexing_status = "indexed"
        item.error_message = None
        await session.commit()
        logger.info("Successfully indexed item %s with %d chunks.", item.id, len(chunks))

    except Exception as exc:
        await session.rollback()
        # In a separate transaction, update the item status to 'failed'
        try:
            item.indexing_status = "failed"
            safe_msg = exc.message if hasattr(exc, "message") else "Embedding indexing service error."
            item.error_message = safe_msg[:500]
            session.add(item)
            await session.commit()
        except Exception as update_err:
            logger.error("Failed to update item failure status: %s", update_err)

        if isinstance(exc, (EmbeddingServiceError, UrlFetchError, AppException)):
            raise
        logger.error("Unexpected error during chunk indexing: %s", exc)
        raise AppException("Failed to process and index knowledge content.", status_code=500)

    return IngestResponse(
        id=item.id,
        title=item.title,
        source_type=item.source_type,
        original_url=item.original_url,
        indexing_status=item.indexing_status,
        chunk_count=len(chunks),
        created_at=item.created_at,
        message="Knowledge item successfully ingested and indexed.",
    )
