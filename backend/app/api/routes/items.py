from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.db.session import get_db
from backend.app.models.knowledge import KnowledgeChunk, KnowledgeItem
from backend.app.schemas.items import KnowledgeItemListResponse, KnowledgeItemResponse

router = APIRouter(tags=["Knowledge Items"])


@router.get(
    "/items",
    response_model=KnowledgeItemListResponse,
    summary="List all saved knowledge items",
)
async def list_items(
    session: AsyncSession = Depends(get_db),
):
    """
    Retrieves all saved notes and URLs, sorted by newest first.
    Includes item IDs, titles, source types, URLs, timestamps, indexing status,
    and chunk counts.
    """
    stmt = (
        select(KnowledgeItem)
        .options(selectinload(KnowledgeItem.chunks))
        .order_by(KnowledgeItem.created_at.desc())
    )
    result = await session.execute(stmt)
    items = result.scalars().all()

    response_items = []
    for item in items:
        # Build clean snippet preview
        raw = item.original_content.strip()
        preview = raw[:200] + "..." if len(raw) > 200 else raw

        response_items.append(
            KnowledgeItemResponse(
                id=item.id,
                title=item.title,
                source_type=item.source_type,
                original_url=item.original_url,
                created_at=item.created_at,
                indexing_status=item.indexing_status,
                error_message=item.error_message,
                chunk_count=len(item.chunks),
                preview=preview,
            )
        )

    return KnowledgeItemListResponse(
        items=response_items,
        total=len(response_items),
    )
