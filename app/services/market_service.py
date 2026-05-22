from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import Market
from app.models.user import User, UserRole
from app.repositories.market_repo import MarketRepository
from app.schemas.base import PaginatedResponse
from app.schemas.markets import MarketCreate, MarketOut


class MarketService:
    def __init__(self, repo: MarketRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def list_paginated(
        self, page: int = 1, limit: int = 20
    ) -> PaginatedResponse[MarketOut]:
        items, total = await self.repo.list_all(self.session, page=page, limit=limit)
        return PaginatedResponse(
            items=[MarketOut.model_validate(m) for m in items],
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
