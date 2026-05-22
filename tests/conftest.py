import asyncio
import threading
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from uuid_extensions import uuid7

import app.core.cache.redis as redis_module
import app.models  # noqa: F401 — registers all models with Base.metadata
from alembic import command
from app.core.cache.redis import create_redis_client, get_redis
from app.core.db.database import get_async_db_url, get_db
from app.main import app as fastapi_app
from app.models import User, UserRole
from app.services.auth_service import AuthService, UserRepository

# ── Schema reset helper — runs in its own thread+loop ─────────────────────────


def _run_schema_reset(db_url: str) -> None:
    async def _reset():
        engine = create_async_engine(db_url, poolclass=NullPool)
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
        await engine.dispose()

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_reset())
    finally:
        loop.close()


# ── Migrations: sync, session-scoped ──────────────────────────────────────────


@pytest.fixture(scope="session", autouse=True)
def run_migrations():
    db_url = get_async_db_url()

    t = threading.Thread(target=_run_schema_reset, args=(db_url,))
    t.start()
    t.join()

    cfg = Config()
    cfg.set_main_option("script_location", "alembic")
    cfg.set_main_option(
        "file_template",
        "%%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s",
    )
    command.upgrade(cfg, "head")
    yield
    command.downgrade(cfg, "base")


# ── Per-test DB session with rollback isolation ────────────────────────────────


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine(get_async_db_url(), poolclass=NullPool)
    connection = await engine.connect()
    transaction = await connection.begin()
    session = async_sessionmaker(bind=connection, expire_on_commit=False)()
    yield session
    await session.close()
    await transaction.rollback()
    await connection.close()
    await engine.dispose()


# ── Redis: patch module-level client AND override the FastAPI dependency ───────


@pytest_asyncio.fixture
async def redis_client():
    client = create_redis_client()
    await client.ping()  # type: ignore
    original = redis_module._redis_client
    redis_module._redis_client = client
    yield client
    redis_module._redis_client = original
    await client.aclose()


# ── HTTP client wired to the test DB session and Redis ────────────────────────


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
    redis_client,
) -> AsyncGenerator[AsyncClient]:
    async def _override_db():
        yield db_session

    def _override_redis():
        return redis_client

    fastapi_app.dependency_overrides[get_db] = _override_db
    fastapi_app.dependency_overrides[get_redis] = _override_redis
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
    ) as ac:
        yield ac
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
async def auth_service(db_session: AsyncSession):
    return AuthService(UserRepository(), db_session)


@pytest.fixture
async def test_user(db_session: AsyncSession, auth_service: AuthService) -> User:
    u = User(
        id=str(uuid7()),
        email="test@example.com",
        role=UserRole.viewer,
        password_hash=auth_service.hash_password("testUserPassword#"),
    )
    db_session.add(u)
    await db_session.flush()
    return u
