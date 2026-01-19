"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import AsyncGenerator
import os
from dotenv import load_dotenv

load_dotenv()

# For SQLite, we'll use sync engine for simplicity
# In production, you'd use async with PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./invoice_reconciliation.db")

# Convert sqlite:// to sqlite+aiosqlite:// for async if needed
if DATABASE_URL.startswith("sqlite://"):
    # Use sync for SQLite for simplicity
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    # For PostgreSQL, use async
    async_engine = create_async_engine(DATABASE_URL)
    SessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
