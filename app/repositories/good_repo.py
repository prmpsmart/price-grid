from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.base_repo import BaseRepository
from app.models.good import Good


class GoodRepository(BaseRepository[Good]):
    model = Good

    async def list_all(self, session: AsyncSession) -> list[Good]:
        result = await session.execute(select(Good).order_by(Good.name))
        return list(result.scalars().all())
