import enum

from sqlmodel import Field

from ..core.db.base_model import BaseModel


class UserRole(enum.StrEnum):
    admin = "admin"
    vendor = "vendor"
    viewer = "viewer"


class User(BaseModel, table=True):
    email: str = Field(max_length=255, unique=True, nullable=False, index=True)
    hashed_password: str = Field(max_length=255, nullable=False)
    role: UserRole = Field(default=UserRole.viewer, nullable=False)
