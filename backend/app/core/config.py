from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ai_inbox",
        description="Async database connection string. Supports PostgreSQL (pgvector) and SQLite (aiosqlite).",
    )

    # AI Configuration
    OPENAI_API_KEY: str = Field(
        default="",
        description="API key for OpenAI or Gemini (used when connecting to OpenAI-compatible endpoints).",
    )
    GEMINI_API_KEY: str = Field(
        default="",
        description="Google Gemini API key.",
    )
    OPENAI_BASE_URL: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta/openai/",
        description="Base URL for OpenAI-compatible client (e.g. Google Gemini endpoint).",
    )
    OPENAI_EMBEDDING_MODEL: str = Field(
        default="gemini-embedding-001",
        description="Embedding model identifier (e.g. gemini-embedding-001 for Gemini, text-embedding-3-small for OpenAI).",
    )
    OPENAI_CHAT_MODEL: str = Field(
        default="gemini-3.5-flash",
        description="Chat completion model identifier (e.g. gemini-3.5-flash or gpt-4o-mini).",
    )
    EMBEDDING_DIMENSION: int = Field(
        default=768,
        description="Vector dimension (768 for Gemini gemini-embedding-001, 1536 for OpenAI text-embedding-3-small).",
    )

    @property
    def effective_api_key(self) -> str:
        """Returns the active API key (prefers GEMINI_API_KEY if populated, otherwise OPENAI_API_KEY)."""
        return self.GEMINI_API_KEY.strip() or self.OPENAI_API_KEY.strip()

    # Application & Security
    FRONTEND_ORIGIN: str = Field(
        default="http://localhost:3000",
        description="Allowed CORS origin for the frontend UI.",
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Application logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    APP_ENV: str = Field(
        default="development",
        description="Runtime environment (development, test, production).",
    )

    # Ingestion & Ingest Limits
    MAX_CONTENT_LENGTH: int = Field(
        default=1_000_000,
        description="Maximum raw note content length in characters (1MB).",
    )
    MAX_URL_RESPONSE_BYTES: int = Field(
        default=5_242_880,
        description="Maximum allowed URL payload size in bytes (5MB).",
    )
    URL_REQUEST_TIMEOUT_SECONDS: float = Field(
        default=10.0,
        description="HTTP request timeout for URL extraction.",
    )

    # Chunking & RAG
    CHUNK_SIZE: int = Field(
        default=500,
        description="Approximate tokens or words per chunk.",
    )
    CHUNK_OVERLAP: int = Field(
        default=80,
        description="Approximate overlap between consecutive chunks.",
    )
    TOP_K_RETRIEVAL: int = Field(
        default=5,
        description="Number of chunks to retrieve for RAG query context.",
    )


settings = Settings()
