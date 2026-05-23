import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal, Annotated, Union, Self
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

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

class PercentageExpenseParticipant(BaseModel):
    user_id: uuid.UUID
    percentage: Decimal = Field(gt=0)

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
    def participants_amount_equal_total_amount(self) -> Self:
        participants_amount = sum(participant.amount for participant in self.participants)

        if participants_amount != self.total_amount:
            raise ValueError('Participants amount must equal total_amount')
        return self

class PercentageExpenseCreateRequest(ExpenseCreateBase):
    split_type: Literal['percentage'] = 'percentage'
    participants: list[PercentageExpenseParticipant]

    @field_validator('participants')
    @classmethod
    def validate_participants(cls, value: list[PercentageExpenseParticipant]) -> list[PercentageExpenseParticipant]:
        if not value:
            raise ValueError('Participants must not be empty')
        return value

    @model_validator(mode='after')
    def participants_total_percentage_equal_to_100(self) -> Self:
        participant_percentage = sum(participant.percentage for participant in self.participants)

        if participant_percentage != Decimal('100'):
            raise ValueError('Participants total percentage must equal to 100%')
        return self

class ExpenseUpdateBase(BaseModel):
    model_config = ConfigDict(extra='forbid')

    payer_id: uuid.UUID | None = None
    title: str | None = None
    description: str | None = None
    total_amount: Decimal | None = None
    expense_date: datetime | None = None

    @field_validator('total_amount')
    @classmethod
    def validate_positive_total_amount(cls, value: Decimal) -> Decimal | None:
        if value is None:
            return value
        if value <= 0:
            raise ValueError('Total amount must be positive')
        return value

class ExpenseUpdateParticipant(BaseModel):
    user_id: uuid.UUID
    amount: Decimal | None = None
    percentage: Decimal | None = None

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return value
        if value <= 0:
            raise ValueError('Amount must be positive')
        return value

    @field_validator('percentage')
    @classmethod
    def validate_percentage(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return value
        if value <= 0:
            raise ValueError('Percentage must be positive')
        return value

class ExpenseUpdateRequest(ExpenseUpdateBase):
    split_type: Literal['equal', 'exact', 'percentage'] | None = None
    participants: list[ExpenseUpdateParticipant] | None = None

    @model_validator(mode='after')
    def validate_split_update_fields(self) -> Self:
        split_fields = [
            self.total_amount is not None,
            self.split_type is not None,
            self.participants is not None,
        ]

        if not any(split_fields):
            return self
        if not all(split_fields):
            raise ValueError('To update splits, all fields must be provided')
        if not self.participants:
            raise ValueError('Participants must not be empty')

        if self.split_type == 'equal':
            for participant in self.participants:
                if participant.amount is not None:
                    raise ValueError('Equal split participants must not include amount')
                if participant.percentage is not None:
                    raise ValueError('Equal split participants must not include percentage')
        if self.split_type == 'exact':
            for participant in self.participants:
                if participant.amount is None:
                    raise ValueError('Exact split participants must include amount')
                if participant.percentage is not None:
                    raise ValueError('Exact split participants must not include percentage')
        if self.split_type == 'percentage':
            for participant in self.participants:
                if participant.amount is not None:
                    raise ValueError('Percentage split participants must not include amount')
                if participant.percentage is None:
                    raise ValueError('Percentage split participants must include percentage')
        return self

ExpenseCreateRequest = Annotated[Union[EqualExpenseCreateRequest, ExactExpenseCreateRequest, PercentageExpenseCreateRequest],
Field(discriminator='split_type')]