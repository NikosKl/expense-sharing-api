import uuid
from sqlalchemy.orm import Session
from app.models import User
from app.schemas.balance import GroupBalancesResponse, UserBalanceResponse
from app.services.exceptions import GroupNotFound, PermissionDeniedError
from app.services.group_member_service import get_group_member
from app.services.group_service import get_group_by_raw_id
from app.services.helpers import calculate_group_balances

def validate_group_balance_access(db: Session, current_user: User, group_id: uuid.UUID) -> None:
    group = get_group_by_raw_id(db, group_id)
    if group is None:
        raise GroupNotFound()
    current_member = get_group_member(db, group_id, current_user.id)
    if current_member is None:
        raise PermissionDeniedError()

def get_group_balances(db: Session, current_user: User, group_id: uuid.UUID) -> GroupBalancesResponse:
    validate_group_balance_access(db, current_user, group_id)

    balances = calculate_group_balances(db, current_user, group_id)

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



