import os
from contextlib import asynccontextmanager
import asyncio
import time
from sqlalchemy.exc import DBAPIError
from datetime import datetime
from typing import AsyncIterator

from sqlalchemy import func
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

DATABASE_URL = os.getenv("DATABASE_URL")

# Pool configuration: allow overrides via env vars
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 5))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", 10))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", 30))

connect_args = (
    {"check_same_thread": False} if DATABASE_URL and "sqlite" in DATABASE_URL else {}
)

engine = create_async_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
)

session_pool: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine, autocommit=False, autoflush=False, expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for declarative models."""

    pass


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """
    Context manager to get a database session.
    Provides a session from the connection pool. The session automatically
    handles transaction lifecycle - commits on success, rolls back on exceptions.
    The session is properly closed after use to return it to the pool.

    Usage:
    ```
    async with get_session() as session:
        result = await session.execute(stmt)
        await session.commit()  # Explicit commit if needed
    ```
    """
    # Simple retry logic for transient connection closure errors
    retries = int(os.getenv("DB_SESSION_RETRIES", 2))
    delay = float(os.getenv("DB_SESSION_RETRY_DELAY", 0.2))

    last_exc = None
    for attempt in range(retries + 1):
        try:
            async with session_pool() as session:
                yield session
                return
        except DBAPIError as e:
            last_exc = e
            # Wait a bit before retrying
            if attempt < retries:
                await asyncio.sleep(delay)
                continue
            raise