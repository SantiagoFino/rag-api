from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.document import Document
from typing import Optional, List
import uuid

class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, title: Optional[str], content: str, description: Optional[str] = None) -> Document:
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
        result = await self.session.execute(
            select(Document).where(Document.id == doc_id)
        )
        return result.scalars().first()

    async def get_all_documents(self) -> List[Document]:
        result = await self.session.execute(
            select(Document)
        )
        return list(result.scalars().all())
