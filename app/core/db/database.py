from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.settings import settings

from ..types.base import Environment
from ..utils.retry import with_retry
from .base_model import BaseModel


def _parse_database_url(db_url: str) -> tuple[str, str | None]:
    """
    Parse database URL and extract asyncpg-incompatible parameters.

    Args:
        db_url: The original database URL

    Returns:
        Tuple of (clean_url, ssl_mode)
    """
    parsed = urlparse(db_url)
    query_params = parse_qs(parsed.query)

    # Extract and remove parameters that asyncpg doesn't support
    ssl_mode = query_params.pop("sslmode", [None])[0]
    # channel_binding is not supported by asyncpg, so we remove it
    _ = query_params.pop("channel_binding", [None])[0]

    # Rebuild the URL without unsupported parameters
    clean_query = urlencode(query_params, doseq=True) if query_params else ""
    clean_url = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            clean_query,
            parsed.fragment,
        )
    )

    return clean_url, ssl_mode


def _convert_to_asyncpg_url(db_url: str) -> str:
    """
    Convert database URL to use asyncpg driver.

    Args:
        db_url: The database URL to convert

    Returns:
        URL with asyncpg driver
    """
    if db_url.startswith("postgres://"):
        return db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://"):
        return db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # If it already has asyncpg, leave it as is
    return db_url


def _get_raw_url() -> str:
    """Return the appropriate raw database URL based on environment."""
    if settings.ENVIRONMENT == Environment.TEST and settings.TEST_DATABASE_URL:
        return str(settings.TEST_DATABASE_URL)
    return str(settings.DATABASE_URL)


def get_sync_db_url() -> str:
    """Return the database URL in sync format (for Alembic migrations)."""
    url = _get_raw_url()
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    elif url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url


def get_async_db_url() -> str:
    """Return the database URL converted to asyncpg format."""
    clean_url, _ = _parse_database_url(_get_raw_url())
    return _convert_to_asyncpg_url(clean_url)


def _get_ssl_config(ssl_mode: str | None) -> dict[str, object]:
    """
    Get SSL configuration for asyncpg based on ssl_mode.

    Args:
        ssl_mode: The SSL mode from the database URL

    Returns:
        SSL configuration dictionary
    """
    connect_args: dict[str, object] = {
        "server_settings": {
            "application_name": settings.SERVICE_NAME,
        }
    }
    if ssl_mode:
        if ssl_mode == "require":
            connect_args["ssl"] = True
        elif ssl_mode == "verify-full":
            connect_args["ssl"] = "verify-full"
        elif ssl_mode == "verify-ca":
            connect_args["ssl"] = "verify-ca"
        # For "disable" or "allow", we don't set ssl parameter
    return connect_args


def get_async_db_engine(test: bool = False) -> AsyncEngine:
    """
    Create and return an async database engine.

    Args:
        test: If True, uses TEST_DATABASE_URL and NullPool (for automated tests).
              If False, uses DATABASE_URL with proper connection pooling.

    Returns:
        AsyncEngine configured for the specified environment.
    """
    # Parse and clean the database URL
    clean_url, ssl_mode = _parse_database_url(_get_raw_url())

    # Convert to asyncpg URL
    db_url = _convert_to_asyncpg_url(clean_url)

    # Get SSL configuration
    connect_args = _get_ssl_config(ssl_mode)

    if test:
        # Use NullPool for tests to avoid connection reuse issues
        return create_async_engine(
            db_url,
            echo=False,
            future=True,
            poolclass=NullPool,
            connect_args=connect_args,
        )
    # Use proper connection pooling for production/development
    return create_async_engine(
        db_url,
        echo=False,
        future=True,
        pool_size=settings.SQL_ALCHEMY_ENGINE_POOL_SIZE,
        max_overflow=settings.SQL_ALCHEMY_ENGINE_MAX_OVERFLOW,
        pool_pre_ping=settings.SQL_ALCHEMY_ENGINE_POOL_PRE_PING,
        pool_recycle=settings.SQL_ALCHEMY_ENGINE_POOL_RECYCLE,
        connect_args=connect_args,
    )


# Create the engine based on environment
engine = get_async_db_engine(test=(settings.ENVIRONMENT == Environment.TEST))

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
)


@asynccontextmanager
async def db_session() -> AsyncGenerator[AsyncSession]:
    """The 'Source of Truth' for session lifecycle."""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db() -> AsyncGenerator[AsyncSession]:
    """FastAPI Dependency that reuses the context manager."""
    async with db_session() as session:
        yield session


async def get_or_create_session(
    session: AsyncSession | None = None,
) -> tuple[AsyncSession, bool]:
    """
    Utility function to get or create database session.

    Args:
        session: Existing session to use, if provided.
                 If not provided, a new session is created.

    Returns:
        Tuple of (session, is_created)
        Basically, if the session is provided,
        it is returned and is_created is False.
        If the session is not provided,
        a new session is created and is_created is True.
    """
    if session:
        return session, False
    new_session = AsyncSessionLocal()
    return new_session, True


@with_retry(max_attempts=3, base_delay=1.0)
async def verify_database_connection() -> None:
    session = AsyncSessionLocal()
    try:
        await session.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    finally:
        await session.close()


async def create_db_and_tables() -> None:
    """Create database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
        logger.info("Database tables created")


async def dispose_engine() -> None:
    """Properly dispose of the database engine."""
    await engine.dispose()
    logger.info("Database engine disposed")
