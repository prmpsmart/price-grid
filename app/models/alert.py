import uuid
from datetime import datetime
from decimal import Decimal

from sqlmodel import DateTime, Field, Index, func

from ..core.db.base_model import BaseModel


class PriceAlert(BaseModel, table=True):
    good_id: uuid.UUID = Field(foreign_key="good.id", nullable=False)
    market_id: uuid.UUID = Field(foreign_key="market.id", nullable=False)

    # Decimal/Numeric columns require max_digits and decimal_places directly in Field
    price: Decimal = Field(max_digits=12, decimal_places=2, nullable=False)
    previous_avg: Decimal = Field(max_digits=12, decimal_places=2, nullable=False)
    delta_pct: Decimal = Field(max_digits=7, decimal_places=4, nullable=False)
    threshold_pct: Decimal = Field(max_digits=7, decimal_places=4, nullable=False)

    currency: str = Field(max_length=3, nullable=False)

    # server_default handles the database-side generation
    triggered_at: datetime = Field(
        sa_column_kwargs={"server_default": func.now()},
        sa_type=DateTime(timezone=True),  # type: ignore
        nullable=False,
    )

    # Indexes are declared inside __table_args__ using the imported SQLModel Index tool
    __table_args__ = (Index("ix_price_alerts_good_market", "good_id", "market_id"),)
