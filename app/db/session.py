import os
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


DATABASE_URL = "postgresql+asyncpg://user:password@localhost/ragdb"

engine = create_async_engine(DATABASE_URL)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def get_db() -> AsyncGenerator:
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()