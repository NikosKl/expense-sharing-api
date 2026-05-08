import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal, Annotated, Union
from pydantic import BaseModel, Field, field_validator, model_validator

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

class EqualExpenseParticipant(BaseModel):
    user_id: uuid.UUID

class ExactExpenseParticipant(BaseModel):
    user_id: uuid.UUID
    amount: Decimal = Field(gt=0)

class ExpenseCreateBase(BaseModel):
    payer_id: uuid.UUID
    title: str
    description: str | None = None
    total_amount: Decimal = Field(gt=0)
    expense_date: datetime

class EqualExpenseCreateRequest(ExpenseCreateBase):
    split_type: Literal['equal'] = 'equal'
    participants: list[EqualExpenseParticipant]

    @field_validator('participants')
    @classmethod

    def validate_participants(cls, value: list[EqualExpenseParticipant]) -> list[EqualExpenseParticipant]:
        if not value:
            raise ValueError('Participants must not be empty')
        return value

class ExactExpenseCreateRequest(ExpenseCreateBase):
    split_type: Literal['exact'] = 'exact'
    participants: list[ExactExpenseParticipant]

    @field_validator('participants')
    @classmethod
    def validate_participants(cls, value: list[ExactExpenseParticipant]) -> list[ExactExpenseParticipant]:
        if not value:
            raise ValueError('Participants must not be empty')
        return value

    @model_validator(mode='after')
    def participants_amount_equal_total_amount(self):
        participants_amount = sum(participant.amount for participant in self.participants)

        if participants_amount != self.total_amount:
            raise ValueError('Participants amount must equal total_amount')
        return self

ExpenseCreateRequest = Annotated[Union[EqualExpenseCreateRequest, ExactExpenseCreateRequest],
Field(discriminator='split_type')]
