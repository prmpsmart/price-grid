import uuid
from datetime import datetime

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.cache.redis import get_redis
from app.core.database.database import get_db
from app.models.user import User
from app.repositories.price_repo import PriceRepository
from app.repositories.vendor_repo import VendorRepository
from app.schemas.prices import PriceCreate, PriceOut
from app.services.price_service import PriceService

router = APIRouter(prefix="/prices", tags=["prices"])


def _get_service(db: AsyncSession = Depends(get_db)) -> PriceService:
    return PriceService(PriceRepository(db), VendorRepository(db))


@router.post("/", response_model=PriceOut, status_code=status.HTTP_201_CREATED)
async def submit_price(
    payload: PriceCreate,
    current_user: User = Depends(get_current_user),
    service: PriceService = Depends(_get_service),
    redis: aioredis.Redis = Depends(get_redis),
):
    try:
        return await service.submit(payload, current_user, redis)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.get("/current", response_model=list[PriceOut])
async def get_current_prices(
    good_id: uuid.UUID | None = Query(None),
    market_id: uuid.UUID | None = Query(None),
    service: PriceService = Depends(_get_service),
    redis: aioredis.Redis = Depends(get_redis),
):
    if good_id and market_id:
        price = await service.get_current(good_id, market_id, redis)
        return [price] if price else []
    return await service.list_all_current()


@router.get("/", response_model=list[PriceOut])
async def list_prices(
    good_id: uuid.UUID | None = Query(None),
    market_id: uuid.UUID | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    service: PriceService = Depends(_get_service),
):
    return await service.list_filtered(good_id, market_id, date_from, date_to)
