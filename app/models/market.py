from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.database import BaseModel


class Market(BaseModel):
    __tablename__ = "markets"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
