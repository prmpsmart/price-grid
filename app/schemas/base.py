from datetime import datetime
from typing import TypeVar

from pydantic import UUID7, BaseModel, ConfigDict

T = TypeVar("T")


class ModelSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID7
    created_at: datetime
    updated_at: datetime


class PaginatedResponse[T: ModelSchema](BaseModel):
    items: list[T]
    total: int
    page: int
    limit: int
