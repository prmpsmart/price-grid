from sqlmodel.ext.asyncio.session import AsyncSession

from ..models.user import User, UserRole
from ..models.vendor import Vendor
from ..repositories.vendor_repo import VendorRepository
from ..schemas import PaginatedResponse, VendorCreate


class VendorService:
    def __init__(self, repo: VendorRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def list_paginated(
        self, page: int = 1, limit: int = 20
    ) -> PaginatedResponse[Vendor]:
        items, total = await self.repo.list_all(self.session, page=page, limit=limit)
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
        )

    async def register(self, payload: VendorCreate, current_user: User) -> Vendor:
        if current_user.role not in (UserRole.vendor, UserRole.admin):
            raise PermissionError(
                "Only vendors and admins can register a vendor profile"
            )
        if await self.repo.get_by_user_id(self.session, str(current_user.id)):
            raise ValueError("A vendor profile already exists for this account")
        return await self.repo.create(
            self.session,
            name=payload.name,
            location=payload.location,
            user_id=current_user.id,
        )
