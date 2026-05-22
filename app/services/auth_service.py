from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenData, UserRegister

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, repo: UserRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    def hash_password(self, password: str) -> str:
        return _pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return _pwd_context.verify(plain, hashed)

    def create_access_token(self, user_id: str) -> str:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        return jwt.encode(
            {"sub": user_id, "exp": expire},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

    def decode_token(self, token: str) -> TokenData:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return TokenData(user_id=payload["sub"])
        except (JWTError, KeyError, ValueError) as exc:
            raise ValueError("Invalid or expired token") from exc

    async def register(self, payload: UserRegister) -> User:
        if await self.repo.get_by_email(self.session, payload.email):
            raise ValueError("Email already registered")
        hashed = self.hash_password(payload.password)
        return await self.repo.create(
            self.session, email=payload.email, hashed_password=hashed, role=payload.role
        )

    async def login(self, email: str, password: str) -> str:
        user = await self.repo.get_by_email(self.session, email)
        if not user or not self.verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        return self.create_access_token(user.id)

    async def get_user_by_id(self, user_id: str) -> User | None:
        return await self.repo.get_by_id(self.session, user_id)
