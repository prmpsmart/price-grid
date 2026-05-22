from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.base_repo import BaseRepository
from app.models.market import Market


class MarketRepository(BaseRepository[Market]):
    model = Market

    async def list_all(self, session: AsyncSession) -> list[Market]:
        result = await session.execute(select(Market).order_by(Market.name))
        return list(result.scalars().all())
