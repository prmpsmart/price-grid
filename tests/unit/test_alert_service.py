from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import UUID7, TypeAdapter
from uuid_extensions import uuid7

from app.models.user import User, UserRole
from app.repositories.alert_repo import AlertRepository
from app.schemas import ThresholdSet
from app.services.alert_service import AlertService

uuid7_adapter = TypeAdapter(UUID7)


def _get_uuid7(str_uuid: Any) -> UUID7:
    return uuid7_adapter.validate_python(str_uuid)


def _make_user(role: UserRole) -> User:
    return User(email="u@test.com", hashed_password="x", role=role)


def _make_threshold_payload() -> ThresholdSet:
    return ThresholdSet(
        good_id=_get_uuid7(uuid7()), market_id=_get_uuid7(uuid7()), threshold_pct=25.0
    )


@pytest.fixture
def alert_repo():
    return AlertRepository()


@pytest.fixture
def service(alert_repo, db_session):
    return AlertService(alert_repo, db_session)


# ── list_all role enforcement ─────────────────────────────────────────────────


async def test_admin_can_list_all_alerts(service, alert_repo):
    admin = _make_user(UserRole.admin)

    with patch.object(alert_repo, "list_all", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = ([], 0)

        result = await service.list_all(admin, page=1, limit=20)

        mock_list.assert_awaited_once()
        assert result.total == 0


async def test_vendor_cannot_list_all_alerts(service):
    vendor = _make_user(UserRole.vendor)

    with pytest.raises(PermissionError, match="Only admins"):
        await service.list_all(vendor)


async def test_viewer_cannot_list_all_alerts(service):
    viewer = _make_user(UserRole.viewer)

    with pytest.raises(PermissionError, match="Only admins"):
        await service.list_all(viewer)


# ── list_by_good — no auth required ──────────────────────────────────────────


async def test_list_by_good_returns_paginated(service, alert_repo):
    good_id = str(uuid7())

    with patch.object(alert_repo, "list_by_good", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = ([], 0)

        result = await service.list_by_good(good_id, page=1, limit=20)

        mock_list.assert_awaited_once()
        assert result.page == 1


# ── set_threshold role enforcement ───────────────────────────────────────────


async def test_admin_can_set_threshold(service, redis_client):
    admin = _make_user(UserRole.admin)
    payload = _make_threshold_payload()
    expected_key = f"spike:threshold:{payload.good_id}:{payload.market_id}"

    await service.set_threshold(payload, admin, redis_client)

    stored = await redis_client.get(expected_key)
    assert stored is not None
    assert stored == str(payload.threshold_pct)


async def test_vendor_cannot_set_threshold(service, redis_client):
    vendor = _make_user(UserRole.vendor)
    payload = _make_threshold_payload()

    with pytest.raises(PermissionError, match="Only admins"):
        await service.set_threshold(payload, vendor, redis_client)

    key = f"spike:threshold:{payload.good_id}:{payload.market_id}"
    assert await redis_client.get(key) is None


async def test_viewer_cannot_set_threshold(service, redis_client):
    viewer = _make_user(UserRole.viewer)
    payload = _make_threshold_payload()

    with pytest.raises(PermissionError, match="Only admins"):
        await service.set_threshold(payload, viewer, redis_client)
