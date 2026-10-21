from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.db.session import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Service Health and Status")
async def health_check(session: AsyncSession = Depends(get_db)):
    """
    Returns service health status and performs a quick database connectivity ping.
    """
    db_healthy = False
    try:
        await session.execute(text("SELECT 1;"))
        db_healthy = True
    except Exception:
        db_healthy = False

    return {
        "status": "healthy" if db_healthy else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database_connected": db_healthy,
        "embedding_model": settings.OPENAI_EMBEDDING_MODEL,
        "embedding_dimension": settings.EMBEDDING_DIMENSION,
        "chat_model": settings.OPENAI_CHAT_MODEL,
        "environment": settings.APP_ENV,
    }
