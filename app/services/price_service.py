import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import redis.asyncio as aioredis
from sqlmodel.ext.asyncio.session import AsyncSession

from ..core.settings import settings
from ..events.publisher import get_spike_threshold, publish_spike_event
from ..models.price import PriceRecord
from ..models.user import User, UserRole
from ..repositories.good_repo import GoodRepository
from ..repositories.market_repo import MarketRepository
from ..repositories.price_repo import PriceRepository
from ..repositories.vendor_repo import VendorRepository
from ..schemas import (
    CompareResponse,
    MarketPriceEntry,
    MarketTrendEntry,
    PaginatedResponse,
    PriceCreate,
    TrendResponse,
)


class PriceService:
    def __init__(
        self,
        repo: PriceRepository,
        vendor_repo: VendorRepository,
        good_repo: GoodRepository,
        market_repo: MarketRepository,
        session: AsyncSession,
    ) -> None:
        self.repo = repo
        self.vendor_repo = vendor_repo
        self.good_repo = good_repo
        self.market_repo = market_repo
        self.session = session

    async def submit(
        self, payload: PriceCreate, current_user: User, redis: aioredis.Redis
    ) -> PriceRecord:
        if current_user.role not in (UserRole.vendor, UserRole.admin):
            raise PermissionError("Only vendors and admins can submit prices")

        if current_user.role == UserRole.vendor:
            vendor = await self.vendor_repo.get_by_user_id(
                self.session,
                str(current_user.id),
            )
            if not vendor or vendor.id != payload.vendor_id:
                raise PermissionError(
                    "Vendors may only submit prices under their own profile"
                )

        record = await self.repo.create(
            self.session,
            good_id=str(payload.good_id),
            vendor_id=str(payload.vendor_id),
            market_id=str(payload.market_id),
            price=Decimal(str(payload.price)),
            currency=payload.currency.upper(),
        )

        await redis.delete(f"price:current:{payload.good_id}:{payload.market_id}")

        avg = await self.repo.get_rolling_average(
            self.session,
            str(payload.good_id),
            str(payload.market_id),
        )
        if avg is not None and avg > 0:
            threshold = await get_spike_threshold(
                redis, str(payload.good_id), str(payload.market_id)
            )
            delta_pct = ((record.price - avg) / avg) * Decimal("100")
            if delta_pct > Decimal(str(threshold)):
                await publish_spike_event(
                    redis,
                    {
                        "good_id": str(payload.good_id),
                        "market_id": str(payload.market_id),
                        "price": str(record.price),
                        "previous_avg": str(avg),
                        "delta_pct": str(delta_pct),
                        "threshold_pct": str(threshold),
                        "currency": record.currency,
                    },
                )

        return record

    async def get_current(
        self, good_id: str, market_id: str, redis: aioredis.Redis
    ) -> PriceRecord | None:
        cache_key = f"price:current:{good_id}:{market_id}"
        cached = await redis.get(cache_key)
        if cached:
            data = json.loads(cached)
            return PriceRecord(**data)
        record = await self.repo.get_latest(self.session, good_id, market_id)
        if not record:
            return None
        await redis.setex(
            cache_key,
            settings.CACHE_TTL_SECONDS,
            record.model_dump_json(),
        )
        return record

    async def list_current_paginated(
        self, page: int = 1, limit: int = 20
    ) -> PaginatedResponse[PriceRecord]:
        items, total = await self.repo.list_current(
            self.session, page=page, limit=limit
        )
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
        )

    async def list_filtered_paginated(
        self,
        good_id: str | None,
        market_id: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[PriceRecord]:
        items, total = await self.repo.list_filtered(
            self.session,
            good_id,
            market_id,
            date_from,
            date_to,
            page=page,
            limit=limit,
        )
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
        )

    async def history(
        self, good_id: str, page: int = 1, limit: int = 20
    ) -> PaginatedResponse[PriceRecord]:
        await self.good_repo.exists_or_raise(
            self.session, good_id, f"Good {good_id} not found"
        )
        items, total = await self.repo.list_filtered(
            self.session,
            good_id=good_id,
            market_id=None,
            date_from=None,
            date_to=None,
            page=page,
            limit=limit,
        )
        return PaginatedResponse(items=items, total=total, page=page, limit=limit)

    async def compare(self, good_id: str) -> CompareResponse:
        good = await self.good_repo.exists_or_raise(
            self.session, good_id, f"Good {good_id} not found"
        )
        records = await self.repo.list_current_for_good(self.session, good_id)
        market_ids = [str(r.market_id) for r in records]
        markets = {
            str(m.id): m
            for m in await self.market_repo.get_by_ids(self.session, market_ids)
        }
        entries = [
            MarketPriceEntry(
                market_id=r.market_id,
                market=markets[str(r.market_id)].name,
                city=markets[str(r.market_id)].city,
                current_price=r.price,
                currency=r.currency,
                submitted_at=r.submitted_at,
            )
            for r in records
            if str(r.market_id) in markets
        ]
        return CompareResponse(
            good_id=good.id,
            good=good.name,
            unit=good.unit,
            markets=entries,
        )

    @staticmethod
    def _parse_window(window: str) -> int:
        if window.endswith("d") and window[:-1].isdigit() and int(window[:-1]) > 0:
            return int(window[:-1])
        raise ValueError(f"Invalid window '{window}'. Use e.g. '7d' or '30d'")

    async def trend(self, good_id: str, window: str) -> TrendResponse:
        good = await self.good_repo.exists_or_raise(
            self.session, good_id, f"Good {good_id} not found"
        )
        days = self._parse_window(window)
        cutoff = datetime.now(UTC) - timedelta(days=days)
        rows = await self.repo.get_market_trends(self.session, good_id, cutoff)
        market_ids = [str(row.market_id) for row in rows]
        markets = {
            str(m.id): m
            for m in await self.market_repo.get_by_ids(self.session, market_ids)
        }
        entries = [
            MarketTrendEntry(
                market_id=row.market_id,
                market=markets[str(row.market_id)].name,
                city=markets[str(row.market_id)].city,
                avg_price=Decimal(str(row.avg_price)).quantize(Decimal("0.01")),
                currency=row.currency,
                data_points=row.data_points,
            )
            for row in rows
            if str(row.market_id) in markets
        ]
        return TrendResponse(
            good_id=good.id,
            good=good.name,
            unit=good.unit,
            window=window,
            markets=entries,
        )
