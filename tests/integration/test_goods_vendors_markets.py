import pytest
from httpx import AsyncClient


# ── Goods ─────────────────────────────────────────────────────────────────────

async def test_admin_can_create_good(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/api/v1/goods",
        json={"name": "Maize", "category": "Grain", "unit": "kg"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Maize"
    assert data["unit"] == "kg"


async def test_viewer_cannot_create_good(client: AsyncClient, viewer_token: str):
    resp = await client.post(
        "/api/v1/goods",
        json={"name": "Maize", "category": "Grain", "unit": "kg"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403


async def test_list_goods_returns_all(client: AsyncClient, admin_token: str):
    await client.post(
        "/api/v1/goods",
        json={"name": "Tomato", "category": "Vegetable", "unit": "kg"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    resp = await client.get("/api/v1/goods")
    assert resp.status_code == 200
    assert any(g["name"] == "Tomato" for g in resp.json())


async def test_list_goods_is_cached(client: AsyncClient, a_good: dict):
    resp1 = await client.get("/api/v1/goods")
    resp2 = await client.get("/api/v1/goods")
    assert resp1.json() == resp2.json()


async def test_create_good_invalidates_cache(client: AsyncClient, admin_token: str, a_good: dict):
    await client.get("/api/v1/goods")  # populate cache
    await client.post(
        "/api/v1/goods",
        json={"name": "Palm Oil", "category": "Oil", "unit": "litre"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    resp = await client.get("/api/v1/goods")
    names = [g["name"] for g in resp.json()]
    assert "Palm Oil" in names


# ── Vendors ───────────────────────────────────────────────────────────────────

async def test_vendor_can_register_profile(client: AsyncClient, vendor_token: str):
    resp = await client.post(
        "/api/v1/vendors",
        json={"name": "Eko Traders", "location": "Lagos Island"},
        headers={"Authorization": f"Bearer {vendor_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Eko Traders"


async def test_viewer_cannot_register_vendor(client: AsyncClient, viewer_token: str):
    resp = await client.post(
        "/api/v1/vendors",
        json={"name": "Ghost Vendor"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403


async def test_duplicate_vendor_profile_returns_400(client: AsyncClient, vendor_token: str):
    payload = {"name": "First Vendor"}
    await client.post("/api/v1/vendors", json=payload, headers={"Authorization": f"Bearer {vendor_token}"})
    resp = await client.post("/api/v1/vendors", json=payload, headers={"Authorization": f"Bearer {vendor_token}"})
    assert resp.status_code == 400


async def test_list_vendors(client: AsyncClient, vendor_with_profile: dict):
    resp = await client.get("/api/v1/vendors")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# ── Markets ───────────────────────────────────────────────────────────────────

async def test_admin_can_create_market(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/api/v1/markets",
        json={"name": "Bodija Market", "city": "Ibadan", "region": "Southwest"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["city"] == "Ibadan"


async def test_viewer_cannot_create_market(client: AsyncClient, viewer_token: str):
    resp = await client.post(
        "/api/v1/markets",
        json={"name": "Ghost Market", "city": "Nowhere", "region": "Nowhere"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403


async def test_list_markets(client: AsyncClient, a_market: dict):
    resp = await client.get("/api/v1/markets")
    assert resp.status_code == 200
    assert any(m["name"] == a_market["name"] for m in resp.json())
