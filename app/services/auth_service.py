import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenData, UserRegister

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    def hash_password(self, password: str) -> str:
        return _pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return _pwd_context.verify(plain, hashed)

    def create_access_token(self, user_id: uuid.UUID) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return jwt.encode({"sub": str(user_id), "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def decode_token(self, token: str) -> TokenData:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return TokenData(user_id=uuid.UUID(payload["sub"]))
        except (JWTError, KeyError, ValueError):
            raise ValueError("Invalid or expired token")

    async def register(self, payload: UserRegister) -> User:
        if await self.repo.get_by_email(payload.email):
            raise ValueError("Email already registered")
        hashed = self.hash_password(payload.password)
        return await self.repo.create(payload.email, hashed, payload.role)

    async def login(self, email: str, password: str) -> str:
        user = await self.repo.get_by_email(email)
        if not user or not self.verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        return self.create_access_token(user.id)

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.repo.get_by_id(user_id)
