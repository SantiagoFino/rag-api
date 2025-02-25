import uvicorn
from fastapi import FastAPI
from app.api.v1.routes import document, chat
from app.db.session import Base, engine


app = FastAPI(title='RAG API', version='1.0.0')


@app.on_event('startup')
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(document.router, prefix="/api/v1", tags=["documents"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])


@app.get("/")
async def root():
    return {"message": "Hello World"}