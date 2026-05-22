from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import Token, UserLogin, UserOut, UserRegister
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer()
_repo = UserRepository()


def _get_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(_repo, db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    service: AuthService = Depends(_get_service),
) -> User:
    try:
        token_data = service.decode_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from exc

    user = await service.get_user_by_id(str(token_data.user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, service: AuthService = Depends(_get_service)):
    try:
        return await service.register(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, service: AuthService = Depends(_get_service)):
    try:
        token = await service.login(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        ) from exc
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
