from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.ingest import IngestRequest, IngestResponse
from backend.app.services.ingestion_service import ingest_knowledge

router = APIRouter(tags=["Ingestion"])


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a note or URL into the knowledge inbox",
)
async def ingest_item(
    request: IngestRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Ingest a new knowledge item (plain-text note or web URL).
    Processes SSRF-safe URL fetching, splits content into semantic chunks,
    generates vector embeddings, and stores them in the vector database.
    """
    return await ingest_knowledge(request=request, session=session)
