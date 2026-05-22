import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.alert_repo import AlertRepository
from app.schemas.alerts import AlertOut, ThresholdSet
from app.schemas.base import PaginatedResponse

_THRESHOLD_KEY = "spike:threshold:{good_id}:{market_id}"


class AlertService:
    def __init__(self, repo: AlertRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def list_all(
        self, current_user: User, page: int = 1, limit: int = 20
    ) -> PaginatedResponse[AlertOut]:
        if current_user.role != UserRole.admin:
            raise PermissionError("Only admins can view all alerts")
        items, total = await self.repo.list_all(self.session, page=page, limit=limit)
        return PaginatedResponse(
            items=[AlertOut.model_validate(a) for a in items],
            total=total,
            page=page,
            limit=limit,
        )

    async def list_by_good(
        self, good_id: str, page: int = 1, limit: int = 20
    ) -> PaginatedResponse[AlertOut]:
        items, total = await self.repo.list_by_good(
            self.session, good_id, page=page, limit=limit
        )
        return PaginatedResponse(
            items=[AlertOut.model_validate(a) for a in items],
            total=total,
            page=page,
            limit=limit,
        )

    async def set_threshold(
        self,
        payload: ThresholdSet,
        current_user: User,
        redis: aioredis.Redis,
    ) -> None:
        if current_user.role != UserRole.admin:
            raise PermissionError("Only admins can set spike thresholds")
        key = _THRESHOLD_KEY.format(
            good_id=payload.good_id, market_id=payload.market_id
        )
        await redis.set(key, str(payload.threshold_pct))
