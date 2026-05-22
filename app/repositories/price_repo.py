from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.base_repo import BaseRepository
from app.models.price import PriceRecord


class PriceRepository(BaseRepository[PriceRecord]):
    model = PriceRecord

    async def get_latest(
        self, session: AsyncSession, good_id: str, market_id: str
    ) -> PriceRecord | None:
        result = await session.execute(
            select(PriceRecord)
            .where(PriceRecord.good_id == good_id, PriceRecord.market_id == market_id)
            .order_by(PriceRecord.submitted_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_current(
        self, session: AsyncSession, *, page: int, limit: int
    ) -> tuple[list[PriceRecord], int]:
        """Latest price per good+market pair."""
        latest_subq = (
            select(
                PriceRecord.good_id,
                PriceRecord.market_id,
                func.max(PriceRecord.submitted_at).label("max_ts"),
            )
            .group_by(PriceRecord.good_id, PriceRecord.market_id)
            .subquery()
        )
        stmt = select(PriceRecord).join(
            latest_subq,
            (PriceRecord.good_id == latest_subq.c.good_id)
            & (PriceRecord.market_id == latest_subq.c.market_id)
            & (PriceRecord.submitted_at == latest_subq.c.max_ts),
        )
        return await self.paginate_offset(session, stmt=stmt, page=page, limit=limit)

    async def list_filtered(
        self,
        session: AsyncSession,
        good_id: str | None = None,
        market_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        *,
        page: int,
        limit: int,
    ) -> tuple[list[PriceRecord], int]:
        stmt = select(PriceRecord).order_by(PriceRecord.submitted_at.desc())
        if good_id:
            stmt = stmt.where(PriceRecord.good_id == good_id)
        if market_id:
            stmt = stmt.where(PriceRecord.market_id == market_id)
        if date_from:
            stmt = stmt.where(PriceRecord.submitted_at >= date_from)
        if date_to:
            stmt = stmt.where(PriceRecord.submitted_at <= date_to)
        return await self.paginate_offset(session, stmt=stmt, page=page, limit=limit)

    async def get_rolling_average(
        self, session: AsyncSession, good_id: str, market_id: str, days: int = 30
    ) -> Decimal | None:
        """30-day rolling average — used by spike detection (Sprint 3)."""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        result = await session.execute(
            select(func.avg(PriceRecord.price)).where(
                PriceRecord.good_id == good_id,
                PriceRecord.market_id == market_id,
                PriceRecord.submitted_at >= cutoff,
            )
        )
        return result.scalar_one_or_none()
