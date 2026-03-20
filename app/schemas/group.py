import uuid
from datetime import datetime
from pydantic import BaseModel

class GroupCreateRequest(BaseModel):
    name: str
    description: str | None = None

class GroupResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {
        'from_attributes': True}
