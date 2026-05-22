import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import UUID as SAUUID
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.db.database import BaseModel


class PriceAlert(BaseModel):
    __tablename__ = "price_alerts"

    good_id: Mapped[uuid.UUID] = mapped_column(
        SAUUID(as_uuid=True), ForeignKey("goods.id"), nullable=False
    )
    market_id: Mapped[uuid.UUID] = mapped_column(
        SAUUID(as_uuid=True), ForeignKey("markets.id"), nullable=False
    )
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    previous_avg: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    delta_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    threshold_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_price_alerts_good_market", "good_id", "market_id"),)
