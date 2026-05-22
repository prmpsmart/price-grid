from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..core.db.base_repo import BaseRepository
from ..models.market import Market


class MarketRepository(BaseRepository[Market]):
    model = Market

    async def list_all(
        self, session: AsyncSession, *, page: int, limit: int
    ) -> tuple[list[Market], int]:
        stmt = select(Market).order_by(Market.name)
        return await self.paginate_offset(session, stmt=stmt, page=page, limit=limit)
