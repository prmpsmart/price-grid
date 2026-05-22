from pydantic import UUID7, BaseModel

from app.schemas.base import ModelSchema


class VendorCreate(BaseModel):
    name: str
    location: str | None = None


class VendorOut(ModelSchema):
    name: str
    location: str | None
    user_id: UUID7
