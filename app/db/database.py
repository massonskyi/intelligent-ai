# app/db/database.py
from sqlmodel import SQLModel, create_engine, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from contextlib import asynccontextmanager

import os

DATABASE_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///history.sqlite")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

async def init_db():
    """Создать таблицы, если не созданы."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

@asynccontextmanager
async def get_session():
    async with AsyncSession(engine) as session:
        yield session
