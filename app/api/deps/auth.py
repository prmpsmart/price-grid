from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from ...core.db.database import get_db
from ...models.user import User
from ...repositories.user_repo import UserRepository
from ...services.auth_service import AuthService

_bearer = HTTPBearer()
_repo = UserRepository()


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(_repo, db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    service: AuthService = Depends(get_auth_service),
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
