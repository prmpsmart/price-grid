from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import Market
from app.models.user import User, UserRole
from app.repositories.market_repo import MarketRepository
from app.schemas.markets import MarketCreate


class MarketService:
    def __init__(self, repo: MarketRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def list_all(self) -> list[Market]:
        return await self.repo.list_all(self.session)

    async def create(self, payload: MarketCreate, current_user: User) -> Market:
        if current_user.role != UserRole.admin:
            raise PermissionError("Only admins can create markets")
        return await self.repo.create(
            self.session,
            name=payload.name,
            city=payload.city,
            region=payload.region,
        )
