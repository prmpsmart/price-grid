from pydantic import UUID7, BaseModel

from app.models.user import UserRole
from app.schemas.base import ModelSchema


class UserRegister(BaseModel):
    email: str
    password: str
    role: UserRole = UserRole.viewer


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: UUID7


class UserOut(ModelSchema):
    email: str
    role: UserRole
