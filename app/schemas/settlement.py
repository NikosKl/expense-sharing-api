import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator


class SettlementCreateRequest(BaseModel):
    payer_id: uuid.UUID
    receiver_id: uuid.UUID
    amount: Decimal = Field(gt=0)
    note: str | None = None
    settled_at: datetime

    @model_validator(mode="after")
    def payer_cannot_equal_receiver(self):
        if self.payer_id == self.receiver_id:
            raise ValueError("payer_id and receiver_id cannot be the same")
        return self

class SettlementResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    payer_id: uuid.UUID
    receiver_id: uuid.UUID
    amount: Decimal
    note: str | None = None
    settled_at: datetime
    created_at: datetime

    model_config = {
        'from_attributes': True
    }