from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.base_repo import BaseRepository
from app.models.vendor import Vendor


class VendorRepository(BaseRepository[Vendor]):
    model = Vendor

    async def list_all(
        self, session: AsyncSession, *, page: int, limit: int
    ) -> tuple[list[Vendor], int]:
        stmt = select(Vendor).order_by(Vendor.name)
        return await self.paginate_offset(session, stmt=stmt, page=page, limit=limit)

    async def get_by_user_id(
        self, session: AsyncSession, user_id: str
    ) -> Vendor | None:
        return await self.get_by(session, user_id=user_id)
