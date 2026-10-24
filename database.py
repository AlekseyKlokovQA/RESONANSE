"""
Database connection and session configuration for Resonance Club Platform
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resonance_club.db")
SYNC_DATABASE_URL = f"sqlite:///{DB_FILE}"
ASYNC_DATABASE_URL = f"sqlite+aiosqlite:///{DB_FILE}"

# Sync engine for seed scripts
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Async engine for FastAPI and SQLAdmin
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


def init_db():
    from models import Base
    Base.metadata.create_all(bind=sync_engine)


async def init_db_async():
    from models import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
