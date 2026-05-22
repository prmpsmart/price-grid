from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.base_repo import BaseRepository
from app.models.vendor import Vendor


class VendorRepository(BaseRepository[Vendor]):
    model = Vendor

    async def list_all(self, session: AsyncSession) -> list[Vendor]:
        result = await session.execute(select(Vendor).order_by(Vendor.name))
        return list(result.scalars().all())

    async def get_by_user_id(
        self, session: AsyncSession, user_id: str
    ) -> Vendor | None:
        return await self.get_by(session, user_id=user_id)
