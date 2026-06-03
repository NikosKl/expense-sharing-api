import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator, field_validator


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
    created_by: uuid.UUID
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

class SettlementUpdateRequest(BaseModel):
    receiver_id: uuid.UUID | None = None
    amount: Decimal | None = None
    note: str | None = None
    settled_at: datetime | None = None

    @field_validator('amount')
    @classmethod
    def amount_validator(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        if value <= 0:
            raise ValueError("Amount must be positive")
        return value