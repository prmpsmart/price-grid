from datetime import datetime

from pydantic import UUID7, BaseModel, ConfigDict


class ModelSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID7
    created_at: datetime
    updated_at: datetime
