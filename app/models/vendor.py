import uuid

from sqlmodel import Field

from ..core.db.base_model import BaseModel


class Vendor(BaseModel, table=True):
    name: str = Field(max_length=255, nullable=False)
    location: str | None = Field(default=None, max_length=255, nullable=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        unique=True,
        ondelete="CASCADE",
    )
