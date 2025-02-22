from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.document import Document
from typing import Optional, List
import uuid

class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, title: str, content: str, description: Optional[str] = None) -> Document:
        doc = Document(
            title=title,
            content=content,
            description=description
        )
        self.session.add(doc)
        await self.session.commit()
        await self.session.refresh(doc)
        return doc

    async def get_by_id(self, doc_id: uuid.UUID) -> Optional[Document]:
        result = await self.session.get(Document, doc_id)
        return result

    async def list_documents(self, skip: int = 0, limit: int = 100) -> List[Document]:
        result = await self.session.execute(
            select(Document).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
