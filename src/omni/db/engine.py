"""Database engine and connection management for OMNI.

Provides async SQLAlchemy engine with connection pooling and
session management.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from omni.core.config import get_settings
from omni.core.exceptions import ConnectionError, DatabaseError
from omni.core.logging import get_db_logger

logger = get_db_logger()

# Global engine instance
_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def create_engine() -> AsyncEngine:
    """Create and configure the async database engine.

    Returns:
        AsyncEngine: Configured SQLAlchemy async engine
    """
    global _engine

    if _engine is not None:
        return _engine

    settings = get_settings()

    try:
        _engine = create_async_engine(
            settings.database.url,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=settings.debug,  # Log SQL in debug mode
        )

        logger.info(
            "Database engine created",
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
        )

        return _engine

    except Exception as e:
        logger.error("Failed to create database engine", error=str(e))
        raise ConnectionError(
            f"Failed to create database engine: {e}",
            details={"url": settings.database.url},
        )


def get_engine() -> AsyncEngine:
    """Get the global engine instance.

    Returns:
        AsyncEngine: The database engine
    """
    if _engine is None:
        return create_engine()
    return _engine


def create_session_maker() -> async_sessionmaker[AsyncSession]:
    """Create the session maker.

    Returns:
        async_sessionmaker: Session factory
    """
    global _session_maker

    if _session_maker is not None:
        return _session_maker

    engine = get_engine()

    _session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    return _session_maker


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session as an async context manager.

    Usage:
        async with get_session() as session:
            result = await session.execute(query)

    Yields:
        AsyncSession: Database session
    """
    session_maker = create_session_maker()
    session = session_maker()

    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error("Session rollback due to error", error=str(e))
        raise
    finally:
        await session.close()


async def close_engine():
    """Close the database engine and dispose of connections.

    Call this on application shutdown.
    """
    global _engine, _session_maker

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_maker = None
        logger.info("Database engine closed")


async def health_check() -> bool:
    """Check database connectivity.

    Returns:
        bool: True if database is reachable
    """
    from sqlalchemy import text

    try:
        engine = get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar()  # Consume the result
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False


# Convenience function for raw SQL queries
async def execute_query(query: str, params: dict | None = None):
    """Execute a raw SQL query.

    Args:
        query: SQL query string
        params: Query parameters

    Returns:
        Query result
    """
    async with get_session() as session:
        result = await session.execute(query, params or {})
        return result
