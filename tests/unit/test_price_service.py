import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pydantic import UUID7, TypeAdapter
from uuid_extensions import uuid7

from app.models.price import PriceRecord
from app.models.user import User, UserRole
from app.models.vendor import Vendor
from app.schemas.prices import PriceCreate
from app.services.price_service import PriceService

_NOW = datetime(2026, 5, 22, 10, 0, 0, tzinfo=UTC)

uuid7_adapter = TypeAdapter(UUID7)


def _get_uuid7(str_uuid: Any) -> UUID7:
    # Safely converts strings or standard UUIDs into a verified Pydantic UUID7
    return uuid7_adapter.validate_python(str_uuid)


def _make_user(role: UserRole) -> User:
    return User(
        id=uuid7(),
        email="u@test.com",
        hashed_password="x",
        role=role,
    )


def _make_vendor(user_id) -> Vendor:
    return Vendor(id=uuid7(), name="V", user_id=user_id)


def _make_payload(vendor_id: UUID7) -> PriceCreate:
    return PriceCreate(
        good_id=_get_uuid7(uuid7()),
        vendor_id=vendor_id,
        market_id=_get_uuid7(uuid7()),
        price=42000.0,
        currency="NGN",
    )


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def mock_vendor_repo():
    return AsyncMock()


@pytest.fixture
def mock_redis():
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.setex = AsyncMock()
    r.delete = AsyncMock()
    return r


@pytest.fixture
def db():
    return AsyncMock()


@pytest.fixture
def service(mock_repo, mock_vendor_repo, db):
    return PriceService(mock_repo, mock_vendor_repo, db)


# ── Role enforcement ──────────────────────────────────────────────────────────


async def test_viewer_cannot_submit(service, mock_redis):
    user = _make_user(UserRole.viewer)
    payload = _make_payload(_get_uuid7(uuid7()))
    with pytest.raises(PermissionError):
        await service.submit(payload, user, mock_redis)


async def test_vendor_can_submit_own_profile(
    service, mock_repo, mock_vendor_repo, mock_redis
):
    user = _make_user(UserRole.vendor)
    vendor = _make_vendor(str(user.id))
    vendor_uuid7 = _get_uuid7(vendor.id)
    payload = _make_payload(vendor_uuid7)

    mock_vendor_repo.get_by_user_id.return_value = vendor
    mock_repo.create.return_value = PriceRecord(
        id=uuid7(),
        good_id=payload.good_id,
        vendor_id=vendor_uuid7,
        market_id=payload.market_id,
        price=Decimal("42000"),
        currency="NGN",
        created_at=_NOW,
        updated_at=_NOW,
    )

    result = await service.submit(payload, user, mock_redis)
    assert result.currency == "NGN"
    mock_redis.delete.assert_called_once()


async def test_vendor_cannot_submit_other_vendor(service, mock_vendor_repo, mock_redis):
    user = _make_user(UserRole.vendor)
    vendor = _make_vendor(str(user.id))
    payload = _make_payload(_get_uuid7(uuid7()))  # different vendor_id

    mock_vendor_repo.get_by_user_id.return_value = vendor

    with pytest.raises(PermissionError, match="own profile"):
        await service.submit(payload, user, mock_redis)


async def test_admin_can_submit_any_vendor(
    service, mock_repo, mock_vendor_repo, mock_redis
):
    user = _make_user(UserRole.admin)
    payload = _make_payload(_get_uuid7(uuid7()))

    mock_repo.create.return_value = PriceRecord(
        id=uuid7(),
        good_id=payload.good_id,
        vendor_id=payload.vendor_id,
        market_id=payload.market_id,
        price=Decimal("42000"),
        currency="NGN",
        created_at=_NOW,
        updated_at=_NOW,
    )

    await service.submit(payload, user, mock_redis)
    mock_vendor_repo.get_by_user_id.assert_not_called()


# ── Cache ─────────────────────────────────────────────────────────────────────


async def test_get_current_cache_hit(service, mock_redis):
    good_id = _get_uuid7(uuid7())
    market_id = _get_uuid7(uuid7())
    cached_data = {
        "id": str(uuid7()),
        "good_id": str(good_id),
        "vendor_id": str(uuid7()),
        "market_id": str(market_id),
        "price": 42000.0,
        "currency": "NGN",
        "submitted_at": "2026-05-22T10:00:00+00:00",
        "created_at": "2026-05-22T10:00:00+00:00",
        "updated_at": "2026-05-22T10:00:00+00:00",
    }
    mock_redis.get.return_value = json.dumps(cached_data)

    result = await service.get_current(good_id, market_id, mock_redis)
    assert result is not None
    assert result.price == 42000.0


async def test_get_current_cache_miss_queries_db(service, mock_repo, mock_redis):
    good_id = _get_uuid7(uuid7())
    market_id = _get_uuid7(uuid7())
    mock_redis.get.return_value = None
    mock_repo.get_latest.return_value = None

    result = await service.get_current(good_id, market_id, mock_redis)
    assert result is None
    mock_repo.get_latest.assert_called_once_with(service.session, good_id, market_id)


async def test_submit_invalidates_cache(
    service, mock_repo, mock_vendor_repo, mock_redis
):
    user = _make_user(UserRole.admin)
    payload = _make_payload(_get_uuid7(uuid7()))
    mock_repo.create.return_value = PriceRecord(
        id=uuid7(),
        good_id=payload.good_id,
        vendor_id=payload.vendor_id,
        market_id=payload.market_id,
        price=Decimal("42000"),
        currency="NGN",
        created_at=_NOW,
        updated_at=_NOW,
    )

    await service.submit(payload, user, mock_redis)

    expected_key = f"price:current:{payload.good_id}:{payload.market_id}"
    mock_redis.delete.assert_called_once_with(expected_key)
