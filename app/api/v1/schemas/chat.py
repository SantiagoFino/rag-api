from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class MessageSchema(BaseModel):
    role: Field(..., pattern="^(user|assistant)$")
    content: str
    created_at: datetime


class ChatSessionSchema(BaseModel):
    id: UUID
    document_id: UUID
    created_at: datetime
    messages: List[MessageSchema] = []


class ChatRequestSchema(BaseModel):
    document_id: UUID
    message: str = Field(..., min_length=1)
    session_id: Optional[UUID] = None


class ChatResponseSchema(BaseModel):
    session_id: UUID
    message: MessageSchema
    context_used: Optional[List[str]] = Field(default=[], description="List of context used")