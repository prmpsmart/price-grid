import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.cache.redis import get_redis
from app.core.db.database import get_db
from app.models.user import User
from app.repositories.good_repo import GoodRepository
from app.schemas.goods import GoodCreate, GoodOut
from app.services.good_service import GoodService

router = APIRouter(prefix="/goods", tags=["goods"])
_repo = GoodRepository()


def _get_service(db: AsyncSession = Depends(get_db)) -> GoodService:
    return GoodService(_repo, db)


@router.get("/", response_model=list[GoodOut])
async def list_goods(
    service: GoodService = Depends(_get_service),
    redis: aioredis.Redis = Depends(get_redis),
):
    return await service.list_all(redis)


@router.post("/", response_model=GoodOut, status_code=status.HTTP_201_CREATED)
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
