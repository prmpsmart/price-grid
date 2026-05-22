from sqlmodel import Field

from ..core.db.base_model import BaseModel


class Market(BaseModel, table=True):
    name: str = Field(max_length=255, nullable=False, unique=True)
    city: str = Field(max_length=100, nullable=False)
    region: str = Field(max_length=100, nullable=False)
