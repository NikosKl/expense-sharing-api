import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class ExpenseParticipantSplit(BaseModel):
    user_id: uuid.UUID

class ExpenseCreateRequest(BaseModel):
    payer_id: uuid.UUID
    title: str
    description: str | None = None
    total_amount: Decimal = Field(gt=0)
    split_type: Literal['equal'] = 'equal'
    expense_date: datetime
    participants: list[ExpenseParticipantSplit]

    @field_validator('participants')
    @classmethod
    def validate_participants(cls, value: list[ExpenseParticipantSplit]) -> list[ExpenseParticipantSplit]:
        if not value:
            raise ValueError('Participants must not be empty')
        return value

class ExpenseSplitResponse(BaseModel):
    id: uuid.UUID
    expense_id: uuid.UUID
    user_id: uuid.UUID
    amount_owed: Decimal
    created_at: datetime

    model_config = {
        'from_attributes': True
    }

class ExpenseResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    created_by: uuid.UUID
    payer_id: uuid.UUID
    title: str
    description: str | None
    total_amount: Decimal
    split_type: str
    expense_date: datetime
    created_at: datetime
    splits: list[ExpenseSplitResponse]

    model_config = {
        'from_attributes': True
    }
