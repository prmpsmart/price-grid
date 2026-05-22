import json
from datetime import datetime
from decimal import Decimal

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.models.price import PriceRecord
from app.models.user import User, UserRole
from app.repositories.price_repo import PriceRepository
from app.repositories.vendor_repo import VendorRepository
from app.schemas.prices import PriceCreate, PriceOut


class PriceService:
    def __init__(
        self,
        repo: PriceRepository,
        vendor_repo: VendorRepository,
        session: AsyncSession,
    ) -> None:
        self.repo = repo
        self.vendor_repo = vendor_repo
        self.session = session

    async def submit(
        self, payload: PriceCreate, current_user: User, redis: aioredis.Redis
    ) -> PriceRecord:
        if current_user.role not in (UserRole.vendor, UserRole.admin):
            raise PermissionError("Only vendors and admins can submit prices")

        if current_user.role == UserRole.vendor:
            vendor = await self.vendor_repo.get_by_user_id(
                self.session, current_user.id
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

        # Sprint 3: spike detection and pub/sub event will be added here

        return record

    async def get_current(
        self, good_id: str, market_id: str, redis: aioredis.Redis
    ) -> PriceOut | None:
        cache_key = f"price:current:{good_id}:{market_id}"
        cached = await redis.get(cache_key)
        if cached:
            return PriceOut(**json.loads(cached))
        record = await self.repo.get_latest(self.session, good_id, market_id)
        if not record:
            return None
        result = PriceOut.model_validate(record)
        await redis.setex(
            cache_key,
            settings.CACHE_TTL_SECONDS,
            json.dumps(result.model_dump(mode="json")),
        )
        return result

    async def list_all_current(self) -> list[PriceRecord]:
        return await self.repo.list_current(self.session)

    async def list_filtered(
        self,
        good_id: str | None,
        market_id: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> list[PriceRecord]:
        return await self.repo.list_filtered(
            self.session, good_id, market_id, date_from, date_to
        )
