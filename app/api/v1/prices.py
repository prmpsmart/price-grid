import uuid
from datetime import datetime

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.cache.redis import get_redis
from app.core.db.database import get_db
from app.models.user import User
from app.repositories.price_repo import PriceRepository
from app.repositories.vendor_repo import VendorRepository
from app.schemas.base import PaginatedResponse
from app.schemas.prices import PriceCreate, PriceOut
from app.services.price_service import PriceService

router = APIRouter(prefix="/prices", tags=["prices"])


def _get_service(db: AsyncSession = Depends(get_db)) -> PriceService:
    return PriceService(
        PriceRepository(),
        VendorRepository(),
        db,
    )


@router.post("", response_model=PriceOut, status_code=status.HTTP_201_CREATED)
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


@router.get("/current", response_model=PaginatedResponse[PriceOut])
async def get_current_prices(
    good_id: uuid.UUID | None = Query(None),
    market_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: PriceService = Depends(_get_service),
    redis: aioredis.Redis = Depends(get_redis),
):
    if good_id and market_id:
        price = await service.get_current(str(good_id), str(market_id), redis)
        items = [price] if price else []
        return PaginatedResponse(items=items, total=len(items), page=page, limit=limit)
    return await service.list_current_paginated(page, limit)


@router.get("", response_model=PaginatedResponse[PriceOut])
async def list_prices(
    good_id: uuid.UUID | None = Query(None),
    market_id: uuid.UUID | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: PriceService = Depends(_get_service),
):
    return await service.list_filtered_paginated(
        str(good_id) if good_id else None,
        str(market_id) if market_id else None,
        date_from,
        date_to,
        page,
        limit,
    )
