from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.database import BaseModel


class Good(BaseModel):
    __tablename__ = "goods"

    name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
