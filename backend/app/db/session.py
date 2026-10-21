from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.base import Base
import backend.app.models.knowledge  # noqa: F401

def get_normalized_database_url(url: str) -> str:
    normalized = url.strip().strip('"').strip("'")
    if normalized.startswith("postgresql://"):
        normalized = normalized.replace("postgresql://", "postgresql+asyncpg://", 1)

    # asyncpg does not accept pgbouncer as a connection argument; we pass statement_cache_size=0 instead
    if "?" in normalized:
        base_part, query_part = normalized.split("?", 1)
        params = [p for p in query_part.split("&") if not p.lower().startswith("pgbouncer=")]
        normalized = base_part + (("?" + "&".join(params)) if params else "")

    return normalized


# Engine configuration
normalized_db_url = get_normalized_database_url(settings.DATABASE_URL)
connect_args = {}

if normalized_db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
elif "asyncpg" in normalized_db_url:
    # Disable statement caching for PgBouncer / Supabase transaction poolers
    connect_args["statement_cache_size"] = 0

engine = create_async_engine(
    normalized_db_url,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initializes the database schema.
    If connected to PostgreSQL, ensures the pgvector extension is enabled
    and builds tables and vector indexes.
    """
    logger.info("Initializing database with URL: %s", settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL)
    
    async with engine.begin() as conn:
        dialect = conn.dialect.name
        if dialect == "postgresql":
            logger.info("PostgreSQL dialect detected. Ensuring 'vector' extension is enabled...")
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            except Exception as e:
                logger.warning("Could not execute CREATE EXTENSION vector. It may require superuser or already exist: %s", e)

        # Create all defined tables
        await conn.run_sync(Base.metadata.create_all)

        # Build HNSW index on embeddings if PostgreSQL
        if dialect == "postgresql":
            try:
                await conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding_hnsw "
                        "ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);"
                    )
                )
                logger.info("pgvector HNSW index initialized.")
            except Exception as e:
                logger.warning("Could not create HNSW vector index: %s", e)

    logger.info("Database schema successfully initialized.")
