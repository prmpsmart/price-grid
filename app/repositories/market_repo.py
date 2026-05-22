from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.base_repo import BaseRepository
from app.models.market import Market


class MarketRepository(BaseRepository[Market]):
    model = Market

    async def list_all(
        self, session: AsyncSession, *, page: int, limit: int
    ) -> tuple[list[Market], int]:
        stmt = select(Market).order_by(Market.name)
        return await self.paginate_offset(session, stmt=stmt, page=page, limit=limit)
