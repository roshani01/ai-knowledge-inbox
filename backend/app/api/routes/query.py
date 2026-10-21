from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.query import QueryRequest, QueryResponse
from backend.app.services.rag import rag_service

router = APIRouter(tags=["Query"])


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Query saved knowledge inbox with natural language",
)
async def query_knowledge(
    request: QueryRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Answers questions using retrieved knowledge chunks with vector similarity search.
    Returns the answer and verifiable source citations tied to saved chunks.
    """
    return await rag_service.answer_question(
        question=request.question,
        session=session,
    )
