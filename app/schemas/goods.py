from pydantic import BaseModel

from app.schemas.base import ModelSchema


class GoodCreate(BaseModel):
    name: str
    category: str
    unit: str
    description: str | None = None


class GoodOut(ModelSchema):
    name: str
    category: str
    unit: str
    description: str | None
