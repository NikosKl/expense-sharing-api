import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal, Self, Annotated, Union

from pydantic import BaseModel, Field, field_validator, model_validator

class RecurringExpenseSplitResponse(BaseModel):
    id: uuid.UUID
    recurring_expense_id: uuid.UUID
    user_id: uuid.UUID
    amount_owed: Decimal
    created_at: datetime

    model_config = {
        'from_attributes': True
    }


class RecurringExpenseResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    created_by: uuid.UUID
    payer_id: uuid.UUID
    title: str
    description: str | None = None
    total_amount: Decimal
    split_type: Literal['equal', 'exact', 'percentage']
    frequency: Literal['daily', 'weekly', 'monthly']
    next_run_at: datetime
    is_active: bool
    created_at: datetime
    splits: list[RecurringExpenseSplitResponse]

    model_config = {
        'from_attributes': True
    }


class EqualRecurringExpenseParticipant(BaseModel):
    user_id: uuid.UUID

class ExactRecurringExpenseParticipant(BaseModel):
    user_id: uuid.UUID
    amount: Decimal = Field(gt=0)

class PercentageRecurringExpenseParticipant(BaseModel):
    user_id: uuid.UUID
    percentage: Decimal = Field(gt=0)


class RecurringExpenseCreateBase(BaseModel):
    payer_id: uuid.UUID
    title: str
    description: str | None = None
    total_amount: Decimal = Field(gt=0)
    frequency: Literal['daily', 'weekly', 'monthly']
    next_run_at: datetime


class EqualRecurringExpenseCreateRequest(RecurringExpenseCreateBase):
    split_type: Literal['equal'] = 'equal'
    participants: list[EqualRecurringExpenseParticipant]

    @field_validator('participants')
    @classmethod
    def validate_participants(cls, value: list[EqualRecurringExpenseParticipant]) -> list[EqualRecurringExpenseParticipant]:
        if not value:
            raise ValueError('Participants must not be empty')
        return value


class ExactRecurringExpenseCreateRequest(RecurringExpenseCreateBase):
    split_type: Literal['exact'] = 'exact'
    participants: list[ExactRecurringExpenseParticipant]

    @field_validator('participants')
    @classmethod
    def validate_participants(cls, value: list[ExactRecurringExpenseParticipant]) -> list[ExactRecurringExpenseParticipant]:
        if not value:
            raise ValueError('Participants must not be empty')
        return value

    @model_validator(mode='after')
    def participants_amount_equal_total_amount(self) -> Self:
        participants_amount = sum(participant.amount for participant in self.participants)

        if participants_amount != self.total_amount:
            raise ValueError('Participants amount must equal total_amount')
        return self


class PercentageRecurringExpenseCreateRequest(RecurringExpenseCreateBase):
    split_type: Literal['percentage'] = 'percentage'
    participants: list[PercentageRecurringExpenseParticipant]

    @field_validator('participants')
    @classmethod
    def validate_participants(cls, value: list[PercentageRecurringExpenseParticipant]) -> list[PercentageRecurringExpenseParticipant]:
        if not value:
            raise ValueError('Participants must not be empty')
        return value

    @model_validator(mode='after')
    def participants_total_percentage_equal_to_100(self) -> Self:
        participant_percentage = sum(participant.percentage for participant in self.participants)

        if participant_percentage != Decimal('100'):
            raise ValueError('Participants total percentage must equal to 100%')
        return self


RecurringExpenseCreateRequest = Annotated[
    Union[EqualRecurringExpenseCreateRequest, ExactRecurringExpenseCreateRequest, PercentageRecurringExpenseCreateRequest],
    Field(discriminator='split_type')]