import uuid
from datetime import datetime

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from ...api.v1.auth import get_current_user
from ...core.cache.redis import get_redis
from ...core.db.database import get_db
from ...models import PriceRecord, User
from ...repositories.good_repo import GoodRepository
from ...repositories.market_repo import MarketRepository
from ...repositories.price_repo import PriceRepository
from ...repositories.vendor_repo import VendorRepository
from ...schemas import CompareResponse, PaginatedResponse, PriceCreate, TrendResponse
from ...services.price_service import PriceService

router = APIRouter(prefix="/prices", tags=["prices"])


def _get_service(db: AsyncSession = Depends(get_db)) -> PriceService:
    return PriceService(
        PriceRepository(),
        VendorRepository(),
        GoodRepository(),
        MarketRepository(),
        db,
    )


@router.post("", response_model=PriceRecord, status_code=status.HTTP_201_CREATED)
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


@router.get("/current", response_model=PaginatedResponse[PriceRecord])
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


@router.get("/history/{good_id}", response_model=PaginatedResponse[PriceRecord])
async def price_history(
    good_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: PriceService = Depends(_get_service),
):
    try:
        return await service.history(str(good_id), page, limit)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get("/compare", response_model=CompareResponse)
async def compare_prices(
    good_id: uuid.UUID = Query(...),
    service: PriceService = Depends(_get_service),
):
    try:
        return await service.compare(str(good_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get("/trends", response_model=TrendResponse)
async def price_trends(
    good_id: uuid.UUID = Query(...),
    window: str = Query("30d"),
    service: PriceService = Depends(_get_service),
):
    try:
        PriceService._parse_window(window)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    try:
        return await service.trend(str(good_id), window)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get("", response_model=PaginatedResponse[PriceRecord])
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
