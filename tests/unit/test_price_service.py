import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import UUID7, TypeAdapter
from uuid_extensions import uuid7

from app.models.price import PriceRecord
from app.models.user import User, UserRole
from app.models.vendor import Vendor
from app.repositories.price_repo import PriceRepository
from app.repositories.vendor_repo import VendorRepository
from app.schemas.prices import PriceCreate
from app.services.price_service import PriceService

_NOW = datetime(2026, 5, 22, 10, 0, 0, tzinfo=UTC)

uuid7_adapter = TypeAdapter(UUID7)


def _get_uuid7(str_uuid: Any) -> UUID7:
    return uuid7_adapter.validate_python(str_uuid)


def _make_user(role: UserRole) -> User:
    return User(id=uuid7(), email="u@test.com", hashed_password="x", role=role)


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


def _make_record(
    payload: PriceCreate, price: Decimal = Decimal("42000")
) -> PriceRecord:
    return PriceRecord(
        id=uuid7(),
        good_id=payload.good_id,
        vendor_id=payload.vendor_id,
        market_id=payload.market_id,
        price=price,
        currency="NGN",
        created_at=_NOW,
        updated_at=_NOW,
    )


@pytest.fixture
def price_repo():
    return PriceRepository()


@pytest.fixture
def vendor_repo():
    return VendorRepository()


@pytest.fixture
def service(price_repo, vendor_repo, db_session):
    return PriceService(price_repo, vendor_repo, db_session)


# ── Role enforcement ──────────────────────────────────────────────────────────


async def test_viewer_cannot_submit(service, redis_client):
    user = _make_user(UserRole.viewer)
    payload = _make_payload(_get_uuid7(uuid7()))
    with pytest.raises(PermissionError):
        await service.submit(payload, user, redis_client)


async def test_vendor_can_submit_own_profile(
    service, price_repo, vendor_repo, redis_client
):
    user = _make_user(UserRole.vendor)
    vendor = _make_vendor(str(user.id))
    vendor_uuid7 = _get_uuid7(vendor.id)
    payload = _make_payload(vendor_uuid7)

    with (
        patch.object(
            vendor_repo, "get_by_user_id", new_callable=AsyncMock
        ) as mock_get_vendor,
        patch.object(price_repo, "create", new_callable=AsyncMock) as mock_create,
        patch.object(
            price_repo, "get_rolling_average", new_callable=AsyncMock
        ) as mock_avg,
    ):
        mock_get_vendor.return_value = vendor
        mock_create.return_value = _make_record(payload)
        mock_avg.return_value = None

        result = await service.submit(payload, user, redis_client)
        assert result.currency == "NGN"
        mock_create.assert_awaited_once()


async def test_vendor_cannot_submit_other_vendor(service, vendor_repo, redis_client):
    user = _make_user(UserRole.vendor)
    vendor = _make_vendor(str(user.id))
    payload = _make_payload(_get_uuid7(uuid7()))  # different vendor_id

    with patch.object(
        vendor_repo, "get_by_user_id", new_callable=AsyncMock
    ) as mock_get_vendor:
        mock_get_vendor.return_value = vendor
        with pytest.raises(PermissionError, match="own profile"):
            await service.submit(payload, user, redis_client)


async def test_admin_can_submit_any_vendor(
    service, price_repo, vendor_repo, redis_client
):
    user = _make_user(UserRole.admin)
    payload = _make_payload(_get_uuid7(uuid7()))

    with (
        patch.object(
            vendor_repo, "get_by_user_id", new_callable=AsyncMock
        ) as mock_get_vendor,
        patch.object(price_repo, "create", new_callable=AsyncMock) as mock_create,
        patch.object(
            price_repo, "get_rolling_average", new_callable=AsyncMock
        ) as mock_avg,
    ):
        mock_create.return_value = _make_record(payload)
        mock_avg.return_value = None

        await service.submit(payload, user, redis_client)
        mock_get_vendor.assert_not_awaited()


# ── Spike detection ───────────────────────────────────────────────────────────


async def test_spike_above_threshold_publishes_event(service, price_repo, redis_client):
    user = _make_user(UserRole.admin)
    payload = _make_payload(_get_uuid7(uuid7()))

    with (
        patch.object(price_repo, "create", new_callable=AsyncMock) as mock_create,
        patch.object(
            price_repo, "get_rolling_average", new_callable=AsyncMock
        ) as mock_avg,
        patch("app.services.price_service.publish_spike_event") as mock_publish,
    ):
        mock_avg.return_value = Decimal("42000")
        mock_create.return_value = _make_record(
            payload, Decimal("52500")
        )  # 25% above avg

        await service.submit(payload, user, redis_client)

        mock_publish.assert_awaited_once()
        event = mock_publish.call_args[0][1]
        assert float(event["delta_pct"]) > 20
        assert event["currency"] == "NGN"


async def test_spike_below_threshold_no_event(service, price_repo, redis_client):
    user = _make_user(UserRole.admin)
    payload = _make_payload(_get_uuid7(uuid7()))

    with (
        patch.object(price_repo, "create", new_callable=AsyncMock) as mock_create,
        patch.object(
            price_repo, "get_rolling_average", new_callable=AsyncMock
        ) as mock_avg,
        patch("app.services.price_service.publish_spike_event") as mock_publish,
    ):
        mock_avg.return_value = Decimal("42000")
        mock_create.return_value = _make_record(
            payload, Decimal("44100")
        )  # 5% above avg

        await service.submit(payload, user, redis_client)
        mock_publish.assert_not_awaited()


async def test_no_average_skips_spike_detection(service, price_repo, redis_client):
    user = _make_user(UserRole.admin)
    payload = _make_payload(_get_uuid7(uuid7()))

    with (
        patch.object(price_repo, "create", new_callable=AsyncMock) as mock_create,
        patch.object(
            price_repo, "get_rolling_average", new_callable=AsyncMock
        ) as mock_avg,
        patch("app.services.price_service.publish_spike_event") as mock_publish,
    ):
        mock_avg.return_value = None
        mock_create.return_value = _make_record(payload, Decimal("99999"))

        await service.submit(payload, user, redis_client)
        mock_publish.assert_not_awaited()


async def test_custom_threshold_respected(service, price_repo, redis_client):
    user = _make_user(UserRole.admin)
    payload = _make_payload(_get_uuid7(uuid7()))
    threshold_key = f"spike:threshold:{payload.good_id}:{payload.market_id}"

    await redis_client.set(threshold_key, "30.0")  # custom 30% threshold

    with (
        patch.object(price_repo, "create", new_callable=AsyncMock) as mock_create,
        patch.object(
            price_repo, "get_rolling_average", new_callable=AsyncMock
        ) as mock_avg,
        patch("app.services.price_service.publish_spike_event") as mock_publish,
    ):
        mock_avg.return_value = Decimal("42000")
        mock_create.return_value = _make_record(
            payload, Decimal("52500")
        )  # 25% above avg

        await service.submit(payload, user, redis_client)
        mock_publish.assert_not_awaited()  # 25% < 30% custom threshold


async def test_price_drop_does_not_trigger_spike(service, price_repo, redis_client):
    user = _make_user(UserRole.admin)
    payload = _make_payload(_get_uuid7(uuid7()))

    with (
        patch.object(price_repo, "create", new_callable=AsyncMock) as mock_create,
        patch.object(
            price_repo, "get_rolling_average", new_callable=AsyncMock
        ) as mock_avg,
        patch("app.services.price_service.publish_spike_event") as mock_publish,
    ):
        mock_avg.return_value = Decimal("42000")
        mock_create.return_value = _make_record(
            payload, Decimal("30000")
        )  # price dropped

        await service.submit(payload, user, redis_client)
        mock_publish.assert_not_awaited()


# ── Cache ─────────────────────────────────────────────────────────────────────


async def test_get_current_cache_hit(service, redis_client):
    good_id = _get_uuid7(uuid7())
    market_id = _get_uuid7(uuid7())
    cache_key = f"price:current:{good_id}:{market_id}"
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
    await redis_client.set(cache_key, json.dumps(cached_data))

    result = await service.get_current(good_id, market_id, redis_client)
    assert result is not None
    assert result.price == 42000.0


async def test_get_current_cache_miss_queries_db(service, price_repo, redis_client):
    good_id = _get_uuid7(uuid7())
    market_id = _get_uuid7(uuid7())

    with patch.object(
        price_repo, "get_latest", new_callable=AsyncMock
    ) as mock_get_latest:
        mock_get_latest.return_value = None
        result = await service.get_current(good_id, market_id, redis_client)

    assert result is None
    mock_get_latest.assert_awaited_once_with(service.session, good_id, market_id)


async def test_submit_invalidates_cache(service, price_repo, redis_client):
    user = _make_user(UserRole.admin)
    payload = _make_payload(_get_uuid7(uuid7()))
    cache_key = f"price:current:{payload.good_id}:{payload.market_id}"

    await redis_client.set(cache_key, "cached_price")

    with (
        patch.object(price_repo, "create", new_callable=AsyncMock) as mock_create,
        patch.object(
            price_repo, "get_rolling_average", new_callable=AsyncMock
        ) as mock_avg,
    ):
        mock_create.return_value = _make_record(payload)
        mock_avg.return_value = None
        await service.submit(payload, user, redis_client)

    assert await redis_client.get(cache_key) is None
