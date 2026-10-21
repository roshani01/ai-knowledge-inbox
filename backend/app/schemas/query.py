from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="Natural language question to ask")

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Question cannot be empty or whitespace only.")
        return stripped


class Citation(BaseModel):
    chunk_id: str
    item_id: str
    title: str
    source_type: str
    url: Optional[str] = None
    snippet: str
    similarity_score: float


class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: List[Citation]
    has_sufficient_context: bool
