from pydantic import BaseModel

from app.schemas.base import ModelSchema


class MarketCreate(BaseModel):
    name: str
    city: str
    region: str


class MarketOut(ModelSchema):
    name: str
    city: str
    region: str
