import pytest
import redis.asyncio as aioredis
from httpx import AsyncClient

from app.core.settings import settings


@pytest.fixture(autouse=True)
async def _clean_redis():
    yield
    client = aioredis.from_url(settings.REDIS_URL)
    await client.flushdb()
    await client.aclose()


@pytest.fixture
async def admin_token(client: AsyncClient) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "admin@test.com", "password": "adminpass", "role": "admin"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "adminpass"},
    )
    return resp.json()["access_token"]


@pytest.fixture
async def vendor_token(client: AsyncClient) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "vendor@test.com", "password": "vendorpass", "role": "vendor"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "vendor@test.com", "password": "vendorpass"},
    )
    return resp.json()["access_token"]


@pytest.fixture
async def viewer_token(client: AsyncClient) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "viewer@test.com", "password": "viewerpass", "role": "viewer"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "viewer@test.com", "password": "viewerpass"},
    )
    return resp.json()["access_token"]


@pytest.fixture
async def vendor_with_profile(client: AsyncClient, vendor_token: str) -> dict:
    resp = await client.post(
        "/api/v1/vendors",
        json={"name": "Test Vendor", "location": "Lagos"},
        headers={"Authorization": f"Bearer {vendor_token}"},
    )
    assert resp.status_code == 201
    return {"token": vendor_token, "vendor_id": resp.json()["id"]}


@pytest.fixture
async def a_good(client: AsyncClient, admin_token: str) -> dict:
    resp = await client.post(
        "/api/v1/goods",
        json={"name": "Rice 50kg", "category": "Grain", "unit": "bag"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
async def a_market(client: AsyncClient, admin_token: str) -> dict:
    resp = await client.post(
        "/api/v1/markets",
        json={"name": "Mile 12 Market", "city": "Lagos", "region": "Southwest"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    return resp.json()
