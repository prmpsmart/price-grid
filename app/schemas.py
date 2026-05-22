from pydantic import UUID7, BaseModel

from .core.db.base_model import BaseModel as DBBaseModel
from .models.user import UserRole


class PaginatedResponse[T: DBBaseModel](BaseModel):
    items: list[T]
    total: int
    page: int
    limit: int


class ThresholdSet(BaseModel):
    good_id: UUID7
    market_id: UUID7
    threshold_pct: float


class UserRegister(BaseModel):
    email: str
    password: str
    role: UserRole = UserRole.viewer


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: UUID7


class GoodCreate(BaseModel):
    name: str
    category: str
    unit: str
    description: str | None = None


class MarketCreate(BaseModel):
    name: str
    city: str
    region: str


class PriceCreate(BaseModel):
    good_id: UUID7
    vendor_id: UUID7
    market_id: UUID7
    price: float
    currency: str


class VendorCreate(BaseModel):
    name: str
    location: str | None = None
