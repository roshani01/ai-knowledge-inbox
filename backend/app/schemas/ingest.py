from datetime import datetime
from typing import Annotated, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator
from backend.app.core.config import settings


class IngestNoteRequest(BaseModel):
    source_type: Literal["note"] = "note"
    title: str = Field(..., min_length=1, max_length=500, description="Title of the text note")
    content: str = Field(..., min_length=1, description="Raw text content of the note")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title cannot be empty or whitespace only.")
        return stripped

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Note content cannot be empty or whitespace only.")
        if len(stripped) > settings.MAX_CONTENT_LENGTH:
            raise ValueError(
                f"Content exceeds maximum allowed size of {settings.MAX_CONTENT_LENGTH} characters."
            )
        return stripped


class IngestUrlRequest(BaseModel):
    source_type: Literal["url"] = "url"
    url: str = Field(..., description="Target webpage URL (HTTP or HTTPS)")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("URL cannot be empty.")
        if not (stripped.startswith("http://") or stripped.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        if len(stripped) > 2048:
            raise ValueError("URL exceeds maximum length of 2048 characters.")
        return stripped


IngestRequest = Annotated[
    Union[IngestNoteRequest, IngestUrlRequest],
    Field(discriminator="source_type"),
]


class IngestResponse(BaseModel):
    id: str
    title: str
    source_type: str
    original_url: Optional[str] = None
    indexing_status: str
    chunk_count: int
    created_at: datetime
    message: str
