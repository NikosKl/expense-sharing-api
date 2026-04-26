from typing import cast

from sqlalchemy import select
import uuid
from decimal import Decimal, ROUND_DOWN
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from app.models import User, Expense, ExpenseSplit
from app.schemas.expense import ExpenseCreateRequest
from app.services.exceptions import InvalidPayerError, InvalidParticipantsError, GroupNotFound, PermissionDeniedError, \
    InvalidExpenseSplitError
from app.services.group_member_service import get_group_member
from app.services.group_service import get_group_by_raw_id

def validate_expense_memberships(db: Session, current_user: User, group_id: uuid.UUID, payer_id: uuid.UUID, participant_ids: list[uuid.UUID]) -> None:
    group = get_group_by_raw_id(db, group_id)
    if group is None:
        raise GroupNotFound()
    current_member = get_group_member(db, group_id, current_user.id)
    if current_member is None:
        raise PermissionDeniedError()
    payer_member = get_group_member(db, group_id, payer_id)
    if payer_member is None:
        raise InvalidPayerError()

    for participant_id in participant_ids:
        participant = get_group_member(db, group_id, participant_id)
        if participant is None:
            raise InvalidParticipantsError()

def calculate_equal_splits(total_amount: Decimal, participant_ids: list[uuid.UUID]) -> list[tuple[uuid.UUID, Decimal]]:
    if not participant_ids:
        raise InvalidParticipantsError()

    participant_count = len(participant_ids)
    cent = Decimal('0.01')

    base_split = (total_amount/participant_count).quantize(cent, rounding=ROUND_DOWN)
    splits = [(participant_id, base_split) for participant_id in participant_ids]

    total_split = base_split * participant_count
    remainder = total_amount - total_split
    extra_cent = int(remainder/cent)

    adjusted_splits = []

    for index, (participant_id, amount) in enumerate(splits):
        if index < extra_cent:
            amount += cent
        adjusted_splits.append((participant_id, amount))

    if sum(amount for _, amount in adjusted_splits) != total_amount:
        raise InvalidExpenseSplitError()

    return adjusted_splits

def create_expense(db: Session, current_user: User, group_id: uuid.UUID, expense_data: ExpenseCreateRequest) -> Expense:
    participant_ids = [participant.user_id for participant in expense_data.participants]

    validate_expense_memberships(db, current_user, group_id, expense_data.payer_id, participant_ids)

    amount_split = calculate_equal_splits(expense_data.total_amount, participant_ids)

    group_expense = Expense(
        group_id=group_id,
        created_by=current_user.id,
        payer_id=expense_data.payer_id,
        title=expense_data.title,
        description=expense_data.description,
        total_amount=expense_data.total_amount,
        split_type=expense_data.split_type,
        expense_date=expense_data.expense_date
    )
    try:
        db.add(group_expense)
        db.flush()

        expense_split = [
            ExpenseSplit(
                expense_id=group_expense.id,
                user_id=participant_id,
                amount_owed=amount
            )
            for participant_id, amount in amount_split
        ]
        db.add_all(expense_split)
        db.commit()
        db.refresh(group_expense)
        return group_expense
    except IntegrityError:
        db.rollback()
        raise

def get_group_expenses(db: Session, current_user: User, group_id: uuid.UUID) -> list[Expense]:
    group = get_group_by_raw_id(db, group_id)
    if group is None:
        raise GroupNotFound()
    current_member = get_group_member(db, group_id, current_user.id)
    if current_member is None:
        raise PermissionDeniedError()

    stmt = select(Expense).where(Expense.group_id == group_id).options(selectinload(Expense.splits)).order_by(Expense.created_at.desc())

    expenses = cast(list[Expense], db.scalars(stmt).all())
    return expenses