from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.base_repo import BaseRepository
from app.models.user import User


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        return await self.get_by(session, email=email)
