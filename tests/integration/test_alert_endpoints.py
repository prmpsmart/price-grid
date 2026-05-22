import datetime
import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid_extensions import uuid7

from app.models.alert import PriceAlert


@pytest_asyncio.fixture
async def an_alert(
    db_session: AsyncSession,
    a_good: dict,
    a_market: dict,
) -> dict:
    alert = PriceAlert(
        good_id=uuid.UUID(a_good["id"]),
        market_id=uuid.UUID(a_market["id"]),
        price=Decimal("52500"),
        previous_avg=Decimal("42000"),
        delta_pct=Decimal("25.0000"),
        threshold_pct=Decimal("20.0000"),
        currency="NGN",
        triggered_at=datetime.datetime.now(datetime.UTC),
    )
    db_session.add(alert)
    await db_session.flush()
    await db_session.refresh(alert)
    return {"id": str(alert.id), "good_id": a_good["id"]}


# ── GET /alerts — admin only ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_can_list_alerts(
    client: AsyncClient, admin_token: str, an_alert: dict
):
    resp = await client.get(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data and "total" in data
    assert data["total"] >= 1
    assert any(a["id"] == an_alert["id"] for a in data["items"])


@pytest.mark.asyncio
async def test_vendor_cannot_list_all_alerts(
    client: AsyncClient, vendor_token: str, an_alert: dict
):
    resp = await client.get(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {vendor_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_viewer_cannot_list_all_alerts(
    client: AsyncClient, viewer_token: str, an_alert: dict
):
    resp = await client.get(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_alerts_requires_auth(client: AsyncClient, an_alert: dict):
    resp = await client.get("/api/v1/alerts")
    assert resp.status_code == 401


# ── GET /alerts/{good_id} — public ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_alerts_by_good(client: AsyncClient, an_alert: dict):
    resp = await client.get(f"/api/v1/alerts/{an_alert['good_id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert all(a["good_id"] == an_alert["good_id"] for a in data["items"])


@pytest.mark.asyncio
async def test_list_alerts_by_unknown_good_returns_empty(client: AsyncClient):
    resp = await client.get(f"/api/v1/alerts/{uuid7()}")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


# ── POST /alerts/thresholds ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_can_set_threshold(
    client: AsyncClient,
    admin_token: str,
    a_good: dict,
    a_market: dict,
):
    resp = await client.post(
        "/api/v1/alerts/thresholds",
        json={
            "good_id": a_good["id"],
            "market_id": a_market["id"],
            "threshold_pct": 30.0,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_viewer_cannot_set_threshold(
    client: AsyncClient,
    viewer_token: str,
    a_good: dict,
    a_market: dict,
):
    resp = await client.post(
        "/api/v1/alerts/thresholds",
        json={
            "good_id": a_good["id"],
            "market_id": a_market["id"],
            "threshold_pct": 25.0,
        },
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403


# ── Pagination ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_alert_list_pagination_shape(
    client: AsyncClient, admin_token: str, an_alert: dict
):
    resp = await client.get(
        "/api/v1/alerts?page=1&limit=5",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["limit"] == 5
    assert len(data["items"]) <= 5
