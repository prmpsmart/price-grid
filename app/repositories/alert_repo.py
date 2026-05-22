from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.base_repo import BaseRepository
from app.models.alert import PriceAlert


class AlertRepository(BaseRepository[PriceAlert]):
    model = PriceAlert

    async def list_all(
        self, session: AsyncSession, *, page: int, limit: int
    ) -> tuple[list[PriceAlert], int]:
        stmt = select(PriceAlert).order_by(PriceAlert.triggered_at.desc())
        return await self.paginate_offset(session, stmt=stmt, page=page, limit=limit)

    async def list_by_good(
        self, session: AsyncSession, good_id: str, *, page: int, limit: int
    ) -> tuple[list[PriceAlert], int]:
        stmt = (
            select(PriceAlert)
            .where(PriceAlert.good_id == good_id)
            .order_by(PriceAlert.triggered_at.desc())
        )
        return await self.paginate_offset(session, stmt=stmt, page=page, limit=limit)
