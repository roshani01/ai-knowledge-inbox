from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class KnowledgeItemResponse(BaseModel):
    id: str
    title: str
    source_type: str
    original_url: Optional[str] = None
    created_at: datetime
    indexing_status: str
    error_message: Optional[str] = None
    chunk_count: int = 0
    preview: str

    model_config = {"from_attributes": True}


class KnowledgeItemListResponse(BaseModel):
    items: List[KnowledgeItemResponse]
    total: int
