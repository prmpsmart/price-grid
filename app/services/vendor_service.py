from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.vendor import Vendor
from app.repositories.vendor_repo import VendorRepository
from app.schemas.vendors import VendorCreate


class VendorService:
    def __init__(self, repo: VendorRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    async def list_all(self) -> list[Vendor]:
        return await self.repo.list_all(self.session)

    async def register(self, payload: VendorCreate, current_user: User) -> Vendor:
        if current_user.role not in (UserRole.vendor, UserRole.admin):
            raise PermissionError(
                "Only vendors and admins can register a vendor profile"
            )
        if await self.repo.get_by_user_id(self.session, current_user.id):
            raise ValueError("A vendor profile already exists for this account")
        return await self.repo.create(
            self.session,
            name=payload.name,
            location=payload.location,
            user_id=current_user.id,
        )
