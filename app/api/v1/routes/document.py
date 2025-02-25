from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.repositories.document import DocumentRepository
from app.db.vector_store import VectorStore, get_vector_store
from app.api.v1.schemas.document import DocumentCreate, DocumentResponse
from app.api.v1.schemas.common import ErrorResponse
from typing import List
import uuid


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/", response_model=DocumentResponse)
async def create_document(document: DocumentCreate, db: AsyncSession = Depends(get_db),
                          vector_store: VectorStore = Depends(get_vector_store)):
    try:
        # stores the info in the postgres db
        document_repo = DocumentRepository(db)
        document = await document_repo.create(title=document.title,
                                              content=document.content,
                                              description=document.description)

        # saves the embeddings in the vector store
        vector_store.add_texts(content=[document.content])

        return document
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(error='Internal Server Error',
                                 detail=str(e)).model_dump())


@router.get("/{document_id}", response_model=List[DocumentResponse])
async def get_document(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    document_repo = DocumentRepository(db)
    document = await document_repo.get_by_id(document_id)

    if not document:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=ErrorResponse(error="Document not found",
                                                 detail="Document not found").model_dump())

    return document
