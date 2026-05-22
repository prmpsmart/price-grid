from sqlmodel.ext.asyncio.session import AsyncSession

from ..models import Market, User, UserRole
from ..repositories.market_repo import MarketRepository
from ..schemas import MarketCreate, PaginatedResponse


class MarketService:
    def __init__(self, repo: MarketRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def list_paginated(
        self, page: int = 1, limit: int = 20
    ) -> PaginatedResponse[Market]:
        items, total = await self.repo.list_all(self.session, page=page, limit=limit)
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
        )

    async def create(self, payload: MarketCreate, current_user: User) -> Market:
        if current_user.role != UserRole.admin:
            raise PermissionError("Only admins can create markets")
        return await self.repo.create(
            self.session,
            name=payload.name,
            city=payload.city,
            region=payload.region,
        )
