import json

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.models.user import User, UserRole
from app.repositories.good_repo import GoodRepository
from app.schemas.goods import GoodCreate, GoodOut

_CACHE_KEY = "goods:list"


class GoodService:
    def __init__(self, repo: GoodRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def list_all(self, redis: aioredis.Redis) -> list[GoodOut]:
        cached = await redis.get(_CACHE_KEY)
        if cached:
            return [GoodOut(**item) for item in json.loads(cached)]
        goods = await self.repo.list_all(self.session)
        result = [GoodOut.model_validate(g) for g in goods]
        await redis.setex(
            _CACHE_KEY,
            settings.CACHE_TTL_SECONDS,
            json.dumps([r.model_dump(mode="json") for r in result]),
        )
        return result

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
