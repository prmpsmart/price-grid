import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.user import UserRole


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
    user_id: uuid.UUID


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}
