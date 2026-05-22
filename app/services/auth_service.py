import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types.token import TokenType
from app.core.utils.exceptions import TokenExpiredError, TokenInvalidError
from app.core.utils.token import token_codec
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenData, UserRegister


class AuthService:
    def __init__(self, repo: UserRepository, session: AsyncSession) -> None:
        self.repo = repo
        self.session = session

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())

    def create_access_token(self, user_id: str) -> str:
        token, _ = token_codec.generate({"sub": user_id}, TokenType.ACCESS)
        return token

    def decode_token(self, token: str) -> TokenData:
        try:
            payload = token_codec.decode(token)
            return TokenData(user_id=payload["sub"])
        except (TokenExpiredError, TokenInvalidError, KeyError) as exc:
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
        return self.create_access_token(str(user.id))

    async def get_user_by_id(self, user_id: str) -> User | None:
        return await self.repo.get_by_id(self.session, user_id)
