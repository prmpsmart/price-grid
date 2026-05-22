from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from ...api.v1.auth import get_current_user
from ...core.db.database import get_db
from ...models import User, Vendor
from ...repositories.vendor_repo import VendorRepository
from ...schemas import PaginatedResponse, VendorCreate
from ...services.vendor_service import VendorService

router = APIRouter(prefix="/vendors", tags=["vendors"])
_repo = VendorRepository()


def _get_service(db: AsyncSession = Depends(get_db)) -> VendorService:
    return VendorService(_repo, db)


@router.get("", response_model=PaginatedResponse[Vendor])
async def list_vendors(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: VendorService = Depends(_get_service),
):
    return await service.list_paginated(page, limit)


@router.post("", response_model=Vendor, status_code=status.HTTP_201_CREATED)
async def register_vendor(
    payload: VendorCreate,
    current_user: User = Depends(get_current_user),
    service: VendorService = Depends(_get_service),
):
    try:
        return await service.register(payload, current_user)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
