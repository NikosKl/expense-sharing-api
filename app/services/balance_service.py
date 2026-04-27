import uuid
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models import User
from app.schemas.balance import GroupBalancesResponse, UserBalanceResponse
from app.services.exceptions import GroupNotFound, PermissionDeniedError
from app.services.expense_service import get_group_expenses
from app.services.group_member_service import get_group_member, get_group_members
from app.services.group_service import get_group_by_raw_id

def validate_group_balance_access(db: Session, current_user: User, group_id: uuid.UUID) -> None:
    group = get_group_by_raw_id(db, group_id)
    if group is None:
        raise GroupNotFound()
    current_member = get_group_member(db, group_id, current_user.id)
    if current_member is None:
        raise PermissionDeniedError()

def get_group_balances(db: Session, current_user: User, group_id: uuid.UUID) -> GroupBalancesResponse:
    validate_group_balance_access(db, current_user, group_id)

    group_members = get_group_members(db, current_user, group_id)

    balances: dict[uuid.UUID, Decimal] = {
        member.user_id: Decimal('0.00')
        for member in group_members
    }

    group_expenses = get_group_expenses(db, current_user, group_id)

    for expense in group_expenses:
        balances[expense.payer_id] = balances.get(expense.payer_id, Decimal('0.00')) + expense.total_amount

        for split in expense.splits:
            balances[split.user_id] = balances.get(split.user_id, Decimal('0.00')) - split.amount_owed

    sorted_balances = sorted(balances.items(), key=lambda item: str(item[0]))

    balance_response = []

    for user_id, amount in sorted_balances:
        balance_response.append(
            UserBalanceResponse(
                user_id=user_id,
                amount=amount
            ))

    return GroupBalancesResponse(
        group_id=group_id,
        balances=balance_response
    )



