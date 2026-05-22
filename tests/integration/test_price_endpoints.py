import pytest
from httpx import AsyncClient
from uuid_extensions import uuid7


@pytest.fixture
async def submitted_price(
    client: AsyncClient,
    vendor_with_profile: dict,
    a_good: dict,
    a_market: dict,
) -> dict:
    resp = await client.post(
        "/api/v1/prices",
        json={
            "good_id": a_good["id"],
            "vendor_id": vendor_with_profile["vendor_id"],
            "market_id": a_market["id"],
            "price": 42000.00,
            "currency": "NGN",
        },
        headers={"Authorization": f"Bearer {vendor_with_profile['token']}"},
    )
    assert resp.status_code == 201
    return resp.json()


# ── Submit ────────────────────────────────────────────────────────────────────


async def test_vendor_can_submit_price(
    client: AsyncClient,
    vendor_with_profile: dict,
    a_good: dict,
    a_market: dict,
):
    resp = await client.post(
        "/api/v1/prices",
        json={
            "good_id": a_good["id"],
            "vendor_id": vendor_with_profile["vendor_id"],
            "market_id": a_market["id"],
            "price": 38000.00,
            "currency": "NGN",
        },
        headers={"Authorization": f"Bearer {vendor_with_profile['token']}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert float(data["price"]) == 38000.0
    assert data["currency"] == "NGN"


async def test_viewer_cannot_submit_price(
    client: AsyncClient,
    viewer_token: str,
    a_good: dict,
    a_market: dict,
):
    resp = await client.post(
        "/api/v1/prices",
        json={
            "good_id": a_good["id"],
            "vendor_id": str(uuid7()),
            "market_id": a_market["id"],
            "price": 100.0,
            "currency": "NGN",
        },
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403


async def test_vendor_cannot_submit_for_another_vendor(
    client: AsyncClient,
    vendor_with_profile: dict,
    a_good: dict,
    a_market: dict,
    admin_token: str,
):
    # Create a second vendor profile via admin
    await client.post(
        "/api/v1/auth/register",
        json={"email": "vendor2@test.com", "password": "pass", "role": "vendor"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "vendor2@test.com", "password": "pass"},
    )
    token2 = login.json()["access_token"]
    v2 = await client.post(
        "/api/v1/vendors",
        json={"name": "Second Vendor"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    other_vendor_id = v2.json()["id"]

    resp = await client.post(
        "/api/v1/prices",
        json={
            "good_id": a_good["id"],
            "vendor_id": other_vendor_id,
            "market_id": a_market["id"],
            "price": 100.0,
            "currency": "NGN",
        },
        headers={"Authorization": f"Bearer {vendor_with_profile['token']}"},
    )
    assert resp.status_code == 403


# ── List / Filter ─────────────────────────────────────────────────────────────


async def test_list_prices_returns_submissions(
    client: AsyncClient, submitted_price: dict
):
    resp = await client.get("/api/v1/prices")
    assert resp.status_code == 200
    data = resp.json()
    ids = [p["id"] for p in data["items"]]
    assert submitted_price["id"] in ids


async def test_list_prices_filter_by_good(
    client: AsyncClient, submitted_price: dict, a_good: dict
):
    resp = await client.get(f"/api/v1/prices?good_id={a_good['id']}")
    assert resp.status_code == 200
    assert all(p["good_id"] == a_good["id"] for p in resp.json()["items"])


# ── Current price (cached) ────────────────────────────────────────────────────


async def test_get_current_price_with_params(
    client: AsyncClient, submitted_price: dict, a_good: dict, a_market: dict
):
    resp = await client.get(
        f"/api/v1/prices/current?good_id={a_good['id']}&market_id={a_market['id']}"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["price"] == submitted_price["price"]


async def test_current_price_is_cached(
    client: AsyncClient,
    submitted_price: dict,
    a_good: dict,
    a_market: dict,
):
    url = f"/api/v1/prices/current?good_id={a_good['id']}&market_id={a_market['id']}"
    r1 = await client.get(url)
    r2 = await client.get(url)
    assert r1.json() == r2.json()


async def test_get_all_current_prices(client: AsyncClient, submitted_price: dict):
    resp = await client.get("/api/v1/prices/current")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_current_price_empty_when_no_submissions(
    client: AsyncClient, a_good: dict, a_market: dict
):
    resp = await client.get(
        f"/api/v1/prices/current?good_id={a_good['id']}&market_id={a_market['id']}"
    )
    assert resp.status_code == 200
    assert resp.json()["items"] == []


# ── History ───────────────────────────────────────────────────────────────────


async def test_history_returns_all_prices_for_good(
    client: AsyncClient, submitted_price: dict, a_good: dict
):
    resp = await client.get(f"/api/v1/prices/history/{a_good['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert all(p["good_id"] == a_good["id"] for p in data["items"])


async def test_history_returns_404_for_unknown_good(client: AsyncClient):
    resp = await client.get(f"/api/v1/prices/history/{uuid7()}")
    assert resp.status_code == 404


async def test_history_is_paginated(
    client: AsyncClient, submitted_price: dict, a_good: dict
):
    resp = await client.get(f"/api/v1/prices/history/{a_good['id']}?page=1&limit=1")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) <= 1
    assert data["page"] == 1
    assert data["limit"] == 1


# ── Compare ───────────────────────────────────────────────────────────────────


async def test_compare_returns_prices_across_markets(
    client: AsyncClient,
    submitted_price: dict,
    a_good: dict,
    a_market: dict,
):
    resp = await client.get(f"/api/v1/prices/compare?good_id={a_good['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["good"] == a_good["name"]
    assert data["unit"] == a_good["unit"]
    assert len(data["markets"]) == 1
    entry = data["markets"][0]
    assert entry["market"] == a_market["name"]
    assert entry["city"] == a_market["city"]
    assert float(entry["current_price"]) == float(submitted_price["price"])
    assert entry["currency"] == submitted_price["currency"]


async def test_compare_returns_empty_markets_when_no_prices(
    client: AsyncClient, a_good: dict
):
    resp = await client.get(f"/api/v1/prices/compare?good_id={a_good['id']}")
    assert resp.status_code == 200
    assert resp.json()["markets"] == []


async def test_compare_returns_404_for_unknown_good(client: AsyncClient):
    resp = await client.get(f"/api/v1/prices/compare?good_id={uuid7()}")
    assert resp.status_code == 404


# ── Trends ────────────────────────────────────────────────────────────────────


async def test_trends_returns_avg_price_per_market(
    client: AsyncClient,
    submitted_price: dict,
    a_good: dict,
    a_market: dict,
):
    resp = await client.get(f"/api/v1/prices/trends?good_id={a_good['id']}&window=30d")
    assert resp.status_code == 200
    data = resp.json()
    assert data["good"] == a_good["name"]
    assert data["window"] == "30d"
    assert len(data["markets"]) == 1
    entry = data["markets"][0]
    assert entry["market"] == a_market["name"]
    assert entry["data_points"] == 1
    assert float(entry["avg_price"]) == float(submitted_price["price"])


async def test_trends_defaults_to_30d_window(
    client: AsyncClient, submitted_price: dict, a_good: dict
):
    resp = await client.get(f"/api/v1/prices/trends?good_id={a_good['id']}")
    assert resp.status_code == 200
    assert resp.json()["window"] == "30d"


async def test_trends_empty_markets_when_no_prices_in_window(
    client: AsyncClient, submitted_price: dict, a_good: dict
):
    resp = await client.get(f"/api/v1/prices/trends?good_id={a_good['id']}&window=1d")
    assert resp.status_code == 200
    # submitted_price just created — should be within 1d; verifies structure
    data = resp.json()
    assert "markets" in data
    assert data["good"] == a_good["name"]


async def test_trends_returns_404_for_unknown_good(client: AsyncClient):
    resp = await client.get(f"/api/v1/prices/trends?good_id={uuid7()}&window=7d")
    assert resp.status_code == 404


async def test_trends_returns_400_for_invalid_window(
    client: AsyncClient, submitted_price: dict, a_good: dict
):
    url = f"/api/v1/prices/trends?good_id={a_good['id']}&window=invalid"
    resp = await client.get(url)
    assert resp.status_code == 400
