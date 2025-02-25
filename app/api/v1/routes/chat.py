from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.repositories.document import DocumentRepository
from app.db.session import get_db
from app.db.repositories.chat import ChatRepository
from app.db.vector_store import get_vector_store
from app.api.v1.schemas.chat import ChatRequestSchema, ChatResponseSchema, MessageSchema
from app.api.v1.schemas.common import ErrorResponse


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponseSchema)
async def chat_with_document(chat_request: ChatRequestSchema, db: AsyncSession = Depends(get_db),
                             vector_store = Depends(get_vector_store)):
    try:
        chat_repo = ChatRepository(db)

        # validates that the doc exists
        document_repository = DocumentRepository(db)
        document = await document_repository.get_by_id(chat_request.document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error="Document not found",
                    detail=f"Document with id {chat_request.document_id} does not exist"
                ).model_dump()
            )

        # if there is no active session, creates a new one
        if not chat_request.session_id:
            session = await chat_repo.create_session(chat_request.document_id)
            session_id = session.id
            conversation_history = []
        else:
            # validate that session exists
            conversation_history = await chat_repo.get_session_messages(chat_request.session_id)
            if not conversation_history:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ErrorResponse(
                        error="Chat session not found",
                        detail=f"Chat session with id {chat_request.session_id} does not exist"
                    ).model_dump()
                )
            session_id = chat_request.session_id

        # adds message to database
        user_message = await chat_repo.add_message(session_id=session_id,
                                                   role='user',
                                                   content=chat_request.message)

        relevant_context = vector_store.similarity_search(chat_request.message)

        # Format conversation history for the LLM
        formatted_history = []
        for msg in conversation_history:
            formatted_history.append({"role": msg.role, "content": msg.content})

        # Add the current user message
        formatted_history.append({"role": "user", "content": chat_request.message})

        mock_response = 'simulated llama response'  # TODO: connect with the LLM

        llm_message = await chat_repo.add_message(session_id=session_id,
                                                  role='assistant',
                                                  content=mock_response,
                                                  metadata={"context_used": relevant_context,
                                                            "history_length": len(conversation_history)})

        return ChatResponseSchema(session_id=session_id,
                                  message=MessageSchema(role='assistant',
                                                        content=mock_response,
                                                        created_at=llm_message.created_at),
                                  context_used=relevant_context)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Internal server error",
                detail=str(e),
                metadata={
                    "document_id": str(chat_request.document_id),
                    "session_id": str(chat_request.session_id) if chat_request.session_id else None
                }
            ).model_dump()
        )


@router.get("/{session_id}/messages", response_model=List[MessageSchema])
async def get_chat_history(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    chat_repo = ChatRepository(db)
    messages = await chat_repo.get_session_messages(session_id)
    if not messages:
        raise HTTPException(status_code=404,
                            detail=ErrorResponse(
                                error="Chat session not found",
                                detail=f"Chat session with id {session_id} does not exist"
                                ).model_dump()
                            )
    return messages
