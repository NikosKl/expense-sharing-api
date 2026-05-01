import uuid
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import User, Settlement
from app.services.expense_service import get_group_expenses
from app.services.group_member_service import get_group_members

def calculate_group_balances(db: Session, current_user: User, group_id: uuid.UUID) -> dict[uuid.UUID, Decimal]:
    group_members = get_group_members(db, current_user, group_id)

    balances: dict[uuid.UUID, Decimal] = {
        member.user_id: Decimal('0.00')
        for member in group_members
    }

    group_expenses = get_group_expenses(db, current_user, group_id)

    for expense in group_expenses:
        balances[expense.payer_id] += expense.total_amount

        for split in expense.splits:
            balances[split.user_id] -= split.amount_owed

    stmt = select(Settlement).where(Settlement.group_id == group_id)
    group_settlements = db.scalars(stmt).all()

    for settlement in group_settlements:
        balances[settlement.payer_id] += settlement.amount
        balances[settlement.receiver_id] -= settlement.amount
    return balances