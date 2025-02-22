from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class DocumentBaseSchema(BaseModel):
    title: Optional[str]
    description: Optional[str] = None


class DocumentCreate(DocumentBaseSchema):
    content: str = Field(..., description="Content of the document")


class DocumentResponse(DocumentBaseSchema):
    id: UUID
    created_at: datetime
    updated_at: datetime
    content_preview: str = Field(..., max_length=200, description="Content preview of the document")

    class Config:
        from_attributes = True
