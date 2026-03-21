import uuid
from datetime import datetime
from pydantic import BaseModel

class GroupMemberCreateRequest(BaseModel):
    user_id: uuid.UUID

class GroupMemberResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    joined_at: datetime

    model_config = {
        "from_attributes": True
    }
