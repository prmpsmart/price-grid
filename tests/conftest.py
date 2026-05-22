import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
import app.models  # noqa: F401 — ensure all models are registered with Base.metadata

# In Docker (--profile test), TEST_DATABASE_URL points to the ephemeral test container.
# In local dev without it set, fall back to a pricegrid_test database on the same host.
TEST_DB_URL = settings.TEST_DATABASE_URL or (
    settings.DATABASE_URL.rsplit("/", 1)[0] + "/pricegrid_test"
)

_engine = create_async_engine(TEST_DB_URL, echo=False)
_SessionFactory = async_sessionmaker(_engine, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
async def _create_tables():
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
async def _clean_tables():
    """Truncate all tables after each test so they start clean."""
    yield
    async with _engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture
async def db() -> AsyncSession:
    async with _SessionFactory() as session:
        yield session


@pytest.fixture
async def client(db: AsyncSession) -> AsyncClient:
    async def _override_db():
        yield db

    app.dependency_overrides[get_db] = _override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
