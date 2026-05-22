import json
import uuid
from datetime import datetime, UTC
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.models.price import PriceRecord
from app.models.user import User, UserRole
from app.models.vendor import Vendor
from app.schemas.prices import PriceCreate
from app.services.price_service import PriceService

_NOW = datetime(2026, 5, 22, 10, 0, 0, tzinfo=UTC)

# use real repos, db session, redis

def _make_user(role: UserRole) -> User:
    return User(
        id=str(uuid.uuid4()), email="u@test.com", hashed_password="x", role=role
    )


def _make_vendor(user_id: str) -> Vendor:
    return Vendor(id=str(uuid.uuid4()), name="V", user_id=user_id)


def _make_payload(vendor_id: uuid.UUID) -> PriceCreate:
    return PriceCreate(
        good_id=uuid.uuid4(),
        vendor_id=vendor_id,
        market_id=uuid.uuid4(),
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
def service(mock_repo, mock_vendor_repo):
    return PriceService(mock_repo, mock_vendor_repo)


# ── Role enforcement ──────────────────────────────────────────────────────────


async def test_viewer_cannot_submit(service, mock_redis):
    user = _make_user(UserRole.viewer)
    payload = _make_payload(uuid.uuid4())
    with pytest.raises(PermissionError):
        await service.submit(payload, user, mock_redis)


async def test_vendor_can_submit_own_profile(
    service, mock_repo, mock_vendor_repo, mock_redis
):
    user = _make_user(UserRole.vendor)
    vendor = _make_vendor(user.id)
    payload = _make_payload(vendor.id)

    mock_vendor_repo.get_by_user_id.return_value = vendor
    mock_repo.create.return_value = PriceRecord(
        id=str(uuid.uuid4()),
        good_id=payload.good_id,
        vendor_id=vendor.id,
        market_id=payload.market_id,
        price=Decimal("42000"),
        currency="NGN",
        date_created=_NOW,
        date_updated=_NOW,
    )

    result = await service.submit(payload, user, mock_redis)
    assert result.currency == "NGN"
    mock_redis.delete.assert_called_once()


async def test_vendor_cannot_submit_other_vendor(service, mock_vendor_repo, mock_redis):
    user = _make_user(UserRole.vendor)
    vendor = _make_vendor(user.id)
    payload = _make_payload(uuid.uuid4())  # different vendor_id

    mock_vendor_repo.get_by_user_id.return_value = vendor

    with pytest.raises(PermissionError, match="own profile"):
        await service.submit(payload, user, mock_redis)


async def test_admin_can_submit_any_vendor(
    service, mock_repo, mock_vendor_repo, mock_redis
):
    user = _make_user(UserRole.admin)
    payload = _make_payload(uuid.uuid4())

    mock_repo.create.return_value = PriceRecord(
        id=str(uuid.uuid4()),
        good_id=payload.good_id,
        vendor_id=payload.vendor_id,
        market_id=payload.market_id,
        price=Decimal("42000"),
        currency="NGN",
        date_created=_NOW,
        date_updated=_NOW,
    )

    await service.submit(payload, user, mock_redis)
    mock_vendor_repo.get_by_user_id.assert_not_called()


# ── Cache ─────────────────────────────────────────────────────────────────────


async def test_get_current_cache_hit(service, mock_redis):
    good_id = uuid.uuid4()
    market_id = uuid.uuid4()
    cached_data = {
        "id": str(uuid.uuid4()),
        "good_id": str(good_id),
        "vendor_id": str(uuid.uuid4()),
        "market_id": str(market_id),
        "price": 42000.0,
        "currency": "NGN",
        "submitted_at": "2026-05-22T10:00:00+00:00",
        "date_created": "2026-05-22T10:00:00+00:00",
        "date_updated": "2026-05-22T10:00:00+00:00",
    }
    mock_redis.get.return_value = json.dumps(cached_data)

    result = await service.get_current(good_id, market_id, mock_redis)
    assert result is not None
    assert result.price == 42000.0


async def test_get_current_cache_miss_queries_db(service, mock_repo, mock_redis):
    good_id = uuid.uuid4()
    market_id = uuid.uuid4()
    mock_redis.get.return_value = None
    mock_repo.get_latest.return_value = None

    result = await service.get_current(good_id, market_id, mock_redis)
    assert result is None
    mock_repo.get_latest.assert_called_once_with(good_id, market_id)


async def test_submit_invalidates_cache(
    service, mock_repo, mock_vendor_repo, mock_redis
):
    user = _make_user(UserRole.admin)
    payload = _make_payload(uuid.uuid4())
    mock_repo.create.return_value = PriceRecord(
        id=str(uuid.uuid4()),
        good_id=payload.good_id,
        vendor_id=payload.vendor_id,
        market_id=payload.market_id,
        price=Decimal("42000"),
        currency="NGN",
        date_created=_NOW,
        date_updated=_NOW,
    )

    await service.submit(payload, user, mock_redis)

    expected_key = f"price:current:{payload.good_id}:{payload.market_id}"
    mock_redis.delete.assert_called_once_with(expected_key)
