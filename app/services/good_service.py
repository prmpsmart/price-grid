import json

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.models.user import User, UserRole
from app.repositories.good_repo import GoodRepository
from app.schemas.base import PaginatedResponse
from app.schemas.goods import GoodCreate, GoodOut

_CACHE_KEY = "goods:list"


class GoodService:
    def __init__(self, repo: GoodRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def list_paginated(
        self, redis: aioredis.Redis, page: int = 1, limit: int = 20
    ) -> PaginatedResponse[GoodOut]:
        cached = await redis.get(_CACHE_KEY)
        if cached:
            all_items = [GoodOut(**item) for item in json.loads(cached)]
        else:
            goods = await self.repo.list_all(self.session)
            all_items = [GoodOut.model_validate(g) for g in goods]
            await redis.setex(
                _CACHE_KEY,
                settings.CACHE_TTL_SECONDS,
                json.dumps([r.model_dump(mode="json") for r in all_items]),
            )
        total = len(all_items)
        start = (page - 1) * limit
        return PaginatedResponse(
            items=all_items[start : start + limit],
            total=total,
            page=page,
            limit=limit,
        )

    async def create(
        self, payload: GoodCreate, current_user: User, redis: aioredis.Redis
    ) -> GoodOut:
        if current_user.role != UserRole.admin:
            raise PermissionError("Only admins can create goods")
        good = await self.repo.create(
            self.session,
            name=payload.name,
            category=payload.category,
            unit=payload.unit,
            description=payload.description,
        )
        await redis.delete(_CACHE_KEY)
        return GoodOut.model_validate(good)
