import uuid
from datetime import datetime

from pydantic import BaseModel

class AuditLogResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    performed_by_id: uuid.UUID
    action: str
    target_type: str
    target_id: uuid.UUID
    details: dict | None
    created_at: datetime
    
    model_config = {
        'from_attributes': True
    }