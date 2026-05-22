import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from ...api.v1.auth import get_current_user
from ...core.cache.redis import get_redis
from ...core.db.database import get_db
from ...models import Good, User
from ...repositories.good_repo import GoodRepository
from ...schemas import GoodCreate, PaginatedResponse
from ...services.good_service import GoodService

router = APIRouter(prefix="/goods", tags=["goods"])
_repo = GoodRepository()


def _get_service(db: AsyncSession = Depends(get_db)) -> GoodService:
    return GoodService(_repo, db)


@router.get("", response_model=PaginatedResponse[Good])
async def list_goods(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: GoodService = Depends(_get_service),
    redis: aioredis.Redis = Depends(get_redis),
):
    return await service.list_paginated(redis, page, limit)


@router.post("", response_model=Good, status_code=status.HTTP_201_CREATED)
async def create_good(
    payload: GoodCreate,
    current_user: User = Depends(get_current_user),
    service: GoodService = Depends(_get_service),
    redis: aioredis.Redis = Depends(get_redis),
):
    try:
        return await service.create(payload, current_user, redis)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
