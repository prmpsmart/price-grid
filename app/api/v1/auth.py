from fastapi import APIRouter, Depends, HTTPException, status

from ...models.user import User
from ...schemas import Token, UserLogin, UserRegister
from ...services.auth_service import AuthService
from ..deps.auth import get_auth_service, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegister, service: AuthService = Depends(get_auth_service)
):
    try:
        user = await service.register(payload)
        data = user.model_dump()
        del data["hashed_password"]
        return data
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, service: AuthService = Depends(get_auth_service)):
    try:
        token = await service.login(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        ) from exc
    return Token(access_token=token)


@router.get("/me", response_model=User)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
