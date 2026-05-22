import uuid
from datetime import datetime
from decimal import Decimal

from sqlmodel import DateTime, Field, Index, func

from ..core.db.base_model import BaseModel


class PriceRecord(BaseModel, table=True):
    good_id: uuid.UUID = Field(foreign_key="good.id", nullable=False)
    vendor_id: uuid.UUID = Field(foreign_key="vendor.id", nullable=False)
    market_id: uuid.UUID = Field(foreign_key="market.id", nullable=False)

    price: Decimal = Field(max_digits=12, decimal_places=2, nullable=False)
    currency: str = Field(max_length=3, nullable=False)

    submitted_at: datetime = Field(
        sa_column_kwargs={"server_default": func.now()},
        sa_type=DateTime(timezone=True),  # type: ignore
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_price_records_good_market_time", "good_id", "market_id", "submitted_at"
        ),
    )
