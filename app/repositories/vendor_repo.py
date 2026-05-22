from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..core.db.base_repo import BaseRepository
from ..models.vendor import Vendor


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
