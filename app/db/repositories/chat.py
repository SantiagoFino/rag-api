from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.chat import ChatSession, Message
from typing import Optional, List
import uuid

class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, document_id: uuid.UUID) -> ChatSession:
        session = ChatSession(document_id=document_id)
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def add_message(
        self,
        session_id: uuid.UUID,
        role: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> Message:
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_session_messages(self, session_id: uuid.UUID) -> List[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)
        )
        return list(result.scalars().all())
