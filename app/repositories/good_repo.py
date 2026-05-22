from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..core.db.base_repo import BaseRepository
from ..models.good import Good


class GoodRepository(BaseRepository[Good]):
    model = Good

    async def list_all(self, session: AsyncSession) -> list[Good]:
        result = await session.exec(
            select(Good).order_by(Good.name),
        )
        return list(result.all())
