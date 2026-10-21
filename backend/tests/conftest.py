import os
import sys
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Force test configuration
os.environ["APP_ENV"] = "test"
os.environ["OPENAI_API_KEY"] = "test-mock-api-key"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from backend.app.core.config import settings

settings.DATABASE_URL = "sqlite+aiosqlite:///:memory:"
settings.OPENAI_API_KEY = "test-mock-api-key"
settings.APP_ENV = "test"

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app

# Create in-memory test engine
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def mock_embedding_vector():
    """Generates a valid 1536-dimensional mock embedding vector."""
    return [0.001 * ((i % 50) + 1) for i in range(settings.EMBEDDING_DIMENSION)]


@pytest.fixture
def mock_openai_embedder(mock_embedding_vector):
    """Mocks the EmbeddingService to avoid live OpenAI API calls in tests."""
    with patch(
        "backend.app.services.embedder.embedding_service.generate_embeddings"
    ) as mock_batch, patch(
        "backend.app.services.embedder.embedding_service.generate_single_embedding"
    ) as mock_single:

        async def fake_batch(texts, batch_size=64):
            return [mock_embedding_vector for _ in texts]

        async def fake_single(text):
            return mock_embedding_vector

        mock_batch.side_effect = fake_batch
        mock_single.side_effect = fake_single
        yield {"batch": mock_batch, "single": mock_single}
