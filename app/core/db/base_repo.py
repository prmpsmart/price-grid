import base64
import binascii
import json
from datetime import datetime
from typing import cast

from sqlalchemy import Select, delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import InstrumentedAttribute

from .base_model import BaseModel

DEFAULT_PAGINATED_LIMIT = 20


class BaseRepository[T: BaseModel]:
    model: type[T]

    async def get_by_id(self, session: AsyncSession, id: str) -> T | None:
        return await session.get(self.model, id)

    async def exists_or_raise(
        self,
        session: AsyncSession,
        id: str,
        error: str = "Record not found",
    ) -> T:
        obj = await self.get_by_id(session, id)
        if not obj:
            raise ValueError(error)
        return obj

    async def get_by_ids(self, session: AsyncSession, ids: list[str]) -> list[T]:
        stmt = select(self.model).where(self.model.id.in_(ids))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    def add(self, session: AsyncSession, instance: T) -> None:
        session.add(instance)

    async def add_and_flush(self, session: AsyncSession, instance: T) -> None:
        self.add(session, instance)
        await session.flush()

    async def add_and_flush_instances(
        self, session: AsyncSession, instances: list[T]
    ) -> None:
        for instance in instances:
            self.add(session, instance)
        await session.flush()

    async def flush_and_refresh(self, session: AsyncSession, instance: T) -> None:
        await self.add_and_flush(session, instance)
        await session.refresh(instance)

    async def load_attributes(
        self,
        session: AsyncSession,
        instance: T,
        attribute_names: list[str],
    ) -> None:
        await session.refresh(instance, attribute_names=attribute_names)

    async def create(self, session: AsyncSession, **kwargs) -> T:
        instance = self.model(**kwargs)
        await self.flush_and_refresh(session, instance)
        return instance

    async def get_by(self, session: AsyncSession, **filters) -> T | None:
        stmt = select(self.model)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by(self, session: AsyncSession, **filters) -> list[T]:
        stmt = select(self.model)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by(self, session: AsyncSession, **filters) -> int:
        stmt = delete(self.model)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        result = await session.execute(stmt)
        return cast(CursorResult, result).rowcount

    async def delete_by_id(self, session: AsyncSession, id: str) -> bool:
        stmt = delete(self.model).where(self.model.id == id)
        result = await session.execute(stmt)
        return cast(CursorResult, result).rowcount > 0

    def encode_timestamp_cursor(self, timestamp: datetime, id: str) -> str:
        payload = {"timestamp": timestamp.isoformat(), "id": id}
        return base64.b64encode(json.dumps(payload).encode()).decode()

    def decode_timestamp_cursor(
        self, cursor: str
    ) -> tuple[datetime | None, str | None]:
        try:
            data = json.loads(base64.b64decode(cursor).decode())
            timestamp, id = data["timestamp"], data["id"]
            assert timestamp and id
            return datetime.fromisoformat(timestamp), id
        except (
            KeyError,
            AssertionError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
            binascii.Error,
        ):
            return None, None

    def apply_timestamp_cursor_pagination(
        self,
        stmt: Select,
        *,
        timestamp_column: InstrumentedAttribute,
        encoded_cursor: str,
        descending: bool = True,
    ) -> Select:
        from sqlalchemy import and_, or_

        cursor_time, cursor_id = self.decode_timestamp_cursor(encoded_cursor)
        if not (cursor_time and cursor_id):
            return stmt

        if descending:
            return stmt.where(
                or_(
                    timestamp_column < cursor_time,
                    and_(timestamp_column == cursor_time, self.model.id < cursor_id),
                )
            )
        return stmt.where(
            or_(
                timestamp_column > cursor_time,
                and_(timestamp_column == cursor_time, self.model.id > cursor_id),
            )
        )

    async def paginate_by_timestamp_cursor(
        self,
        session: AsyncSession,
        *,
        stmt: Select,
        timestamp_column: InstrumentedAttribute,
        limit: int = DEFAULT_PAGINATED_LIMIT,
        encoded_cursor: str | None = None,
    ) -> tuple[list[T], str | None]:
        from sqlalchemy import desc

        stmt = stmt.order_by(desc(timestamp_column), desc(self.model.id)).limit(
            limit + 1
        )

        if encoded_cursor:
            stmt = self.apply_timestamp_cursor_pagination(
                stmt,
                timestamp_column=timestamp_column,
                encoded_cursor=encoded_cursor,
            )

        result = await session.execute(stmt)
        items = list(result.scalars().all())
        has_more = len(items) > limit

        if has_more:
            items = items[:limit]

        next_cursor = None
        if has_more and items:
            last = items[-1]
            next_cursor = self.encode_timestamp_cursor(
                getattr(last, timestamp_column.key), last.id
            )

        return items, next_cursor
