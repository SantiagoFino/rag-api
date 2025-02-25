import uvicorn
from fastapi import FastAPI
from app.api.v1.routes import document, chat
from app.db.session import Base, engine, async_session
from app.db.vector_store import VectorStore
from app.db.repositories.document import DocumentRepository


app = FastAPI(title='RAG API', version='1.0.0')


@app.on_event('startup')
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def initialize_vector_store():
    vector_store = VectorStore.get_instance()

    async with async_session() as session:
        # Get document repository
        doc_repo = DocumentRepository(session)

        documents = await doc_repo.get_all_documents()

        texts = []
        for doc in documents:
            if hasattr(doc, 'content'):
                texts.append(doc.content)

        if texts:
            vector_store.add_texts(texts)


app.include_router(document.router, prefix="/api/v1", tags=["documents"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])


@app.get("/")
async def root():
    return {"message": "Hello World"}