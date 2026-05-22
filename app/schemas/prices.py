from datetime import datetime

from pydantic import UUID7, BaseModel

from app.schemas.base import ModelSchema


class PriceCreate(BaseModel):
    good_id: UUID7
    vendor_id: UUID7
    market_id: UUID7
    price: float
    currency: str


class PriceOut(ModelSchema):
    good_id: UUID7
    vendor_id: UUID7
    market_id: UUID7
    price: float
    currency: str
    submitted_at: datetime
