from sqlmodel.ext.asyncio.session import AsyncSession

from ..core.db.base_repo import BaseRepository
from ..models.user import User


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        return await self.get_by(session, email=email)
