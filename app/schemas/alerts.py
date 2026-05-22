from datetime import datetime
from decimal import Decimal

from pydantic import UUID7, BaseModel

from app.schemas.base import ModelSchema


class AlertOut(ModelSchema):
    good_id: UUID7
    market_id: UUID7
    price: Decimal
    previous_avg: Decimal
    delta_pct: Decimal
    threshold_pct: Decimal
    currency: str
    triggered_at: datetime


class ThresholdSet(BaseModel):
    good_id: UUID7
    market_id: UUID7
    threshold_pct: float
