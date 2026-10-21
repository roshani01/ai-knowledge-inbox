from typing import List, Tuple
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.knowledge import KnowledgeChunk, KnowledgeItem


async def search_similar_chunks(
    session: AsyncSession,
    query_embedding: List[float],
    limit: int = settings.TOP_K_RETRIEVAL,
) -> List[Tuple[KnowledgeChunk, KnowledgeItem, float]]:
    """
    Retrieves the top-k most relevant chunks using cosine similarity against the query embedding.
    Uses pgvector's native cosine distance operator (<=>) on PostgreSQL,
    and falls back to in-memory cosine similarity on SQLite.
    Returns: List of (KnowledgeChunk, KnowledgeItem, similarity_score).
    """
    bind = session.bind
    dialect_name = bind.dialect.name if bind else "postgresql"

    if dialect_name == "postgresql":
        try:
            distance_expr = KnowledgeChunk.embedding.cosine_distance(query_embedding).label("distance")
            stmt = (
                select(KnowledgeChunk, KnowledgeItem, distance_expr)
                .join(KnowledgeItem, KnowledgeChunk.item_id == KnowledgeItem.id)
                .where(KnowledgeItem.indexing_status == "indexed")
                .order_by(distance_expr)
                .limit(limit)
            )
            result = await session.execute(stmt)
            rows = result.all()
            return [
                (chunk, item, float(max(0.0, min(1.0, 1.0 - float(dist)))))
                for chunk, item, dist in rows
            ]
        except Exception as e:
            logger.error("Error executing pgvector cosine search: %s", e)
            raise

    # Fallback for SQLite / unit testing without pgvector
    stmt = (
        select(KnowledgeChunk, KnowledgeItem)
        .join(KnowledgeItem, KnowledgeChunk.item_id == KnowledgeItem.id)
        .where(KnowledgeItem.indexing_status == "indexed")
    )
    result = await session.execute(stmt)
    rows = result.all()
    if not rows:
        return []

    q_vec = np.array(query_embedding, dtype=np.float32)
    q_norm = float(np.linalg.norm(q_vec))
    if q_norm == 0.0:
        return []

    scored_chunks: List[Tuple[KnowledgeChunk, KnowledgeItem, float]] = []
    for chunk, item in rows:
        c_vec = np.array(chunk.embedding, dtype=np.float32)
        c_norm = float(np.linalg.norm(c_vec))
        if c_norm > 0:
            sim = float(np.dot(q_vec, c_vec) / (q_norm * c_norm))
        else:
            sim = 0.0
        # Bound similarity between 0 and 1
        sim = max(0.0, min(1.0, sim))
        scored_chunks.append((chunk, item, sim))

    scored_chunks.sort(key=lambda x: x[2], reverse=True)
    return scored_chunks[:limit]
