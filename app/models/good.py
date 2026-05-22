from sqlmodel import Field

from ..core.db.base_model import BaseModel


class Good(BaseModel, table=True):
    name: str = Field(max_length=255, nullable=False, unique=True, index=True)
    category: str = Field(max_length=100, nullable=False)
    unit: str = Field(max_length=50, nullable=False)
    description: str | None = Field(default=None, max_length=65535, nullable=True)
