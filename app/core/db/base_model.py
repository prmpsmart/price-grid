import uuid
from datetime import UTC, datetime

from sqlmodel import DateTime, Field, SQLModel
from uuid_extensions import uuid7


class BaseModel(SQLModel):
    id: uuid.UUID = Field(
        default_factory=uuid7,
        primary_key=True,
        nullable=False,
    )

    # Force the database schema to use TIMESTAMP WITH TIME ZONE
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore
        nullable=False,
    )

    # Do the exact same thing for updated_at
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
        nullable=False,
    )
