import sys
from pathlib import Path

# Ensure root directory is on sys.path so 'backend.app' imports succeed when running from backend/
_backend_dir = Path(__file__).resolve().parent.parent
_repo_root = _backend_dir.parent

for _p in (str(_repo_root), str(_backend_dir)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.ingest import router as ingest_router
from backend.app.api.routes.items import router as items_router
from backend.app.api.routes.query import router as query_router
from backend.app.core.config import settings
from backend.app.core.errors import register_exception_handlers
from backend.app.core.logging import logger
from backend.app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Knowledge Inbox API...")
    try:
        await init_db()
    except Exception as e:
        logger.error("Failed to initialize database on startup: %s", e)
    yield
    logger.info("Shutting down AI Knowledge Inbox API...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Knowledge Inbox API",
        description=(
            "Production-minded API for saving notes and URLs, generating embeddings, "
            "and performing grounded question-answering with vector similarity retrieval and citations."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS Configuration
    allowed_origins = [
        settings.FRONTEND_ORIGIN.rstrip("/"),
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Exception Handlers
    register_exception_handlers(app)

    # Register Routes
    app.include_router(health_router)
    app.include_router(ingest_router)
    app.include_router(items_router)
    app.include_router(query_router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
