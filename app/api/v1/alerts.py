import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.cache.redis import get_redis
from app.core.db.database import get_db
from app.models.user import User
from app.repositories.alert_repo import AlertRepository
from app.schemas.alerts import AlertOut, ThresholdSet
from app.schemas.base import PaginatedResponse
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])
_repo = AlertRepository()


def _get_service(db: AsyncSession = Depends(get_db)) -> AlertService:
    return AlertService(_repo, db)


@router.get("", response_model=PaginatedResponse[AlertOut])
async def list_alerts(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: AlertService = Depends(_get_service),
):
    try:
        return await service.list_all(current_user, page, limit)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc


@router.post("/thresholds", status_code=status.HTTP_204_NO_CONTENT)
async def set_spike_threshold(
    payload: ThresholdSet,
    current_user: User = Depends(get_current_user),
    service: AlertService = Depends(_get_service),
    redis: aioredis.Redis = Depends(get_redis),
):
    try:
        await service.set_threshold(payload, current_user, redis)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc


@router.get("/{good_id}", response_model=PaginatedResponse[AlertOut])
async def list_alerts_by_good(
    good_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: AlertService = Depends(_get_service),
):
    return await service.list_by_good(str(good_id), page, limit)
