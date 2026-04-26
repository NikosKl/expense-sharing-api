import uuid
from decimal import Decimal
from pydantic import BaseModel

class UserBalanceResponse(BaseModel):
    user_id: uuid.UUID
    amount: Decimal

    model_config = {
        'from_attributes': True
    }

class GroupBalancesResponse(BaseModel):
    group_id: uuid.UUID
    balances: list[UserBalanceResponse]

    model_config = {
        'from_attributes': True
    }