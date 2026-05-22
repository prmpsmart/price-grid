from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.db.database import get_db
from app.models.user import User
from app.repositories.market_repo import MarketRepository
from app.schemas.base import PaginatedResponse
from app.schemas.markets import MarketCreate, MarketOut
from app.services.market_service import MarketService

router = APIRouter(prefix="/markets", tags=["markets"])
_repo = MarketRepository()


def _get_service(db: AsyncSession = Depends(get_db)) -> MarketService:
    return MarketService(_repo, db)


@router.get("", response_model=PaginatedResponse[MarketOut])
async def list_markets(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: MarketService = Depends(_get_service),
):
    return await service.list_paginated(page, limit)


@router.post("", response_model=MarketOut, status_code=status.HTTP_201_CREATED)
async def create_market(
    payload: MarketCreate,
    current_user: User = Depends(get_current_user),
    service: MarketService = Depends(_get_service),
):
    try:
        return await service.create(payload, current_user)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
