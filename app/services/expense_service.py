from typing import cast
from sqlalchemy import select, delete
import uuid
from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from app.models import User, Expense, ExpenseSplit
from app.schemas.expense import ExpenseCreateRequest, ExactExpenseCreateRequest, EqualExpenseCreateRequest, \
    PercentageExpenseCreateRequest, ExpenseUpdateRequest
from app.services.exceptions import InvalidPayerError, InvalidParticipantsError, GroupNotFound, PermissionDeniedError, \
    InvalidExpenseSplitError, ExpenseNotFound
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

def calculate_exact_splits(total_amount: Decimal, participant_splits: list[tuple[uuid.UUID, Decimal]]) -> list[tuple[uuid.UUID, Decimal]]:
    if not participant_splits:
        raise InvalidParticipantsError()

    if sum(amount for _, amount in participant_splits) != total_amount:
        raise InvalidExpenseSplitError()
    return participant_splits

def calculate_percentage_splits(total_amount: Decimal, participant_splits: list[tuple[uuid.UUID, Decimal]]) -> list[tuple[uuid.UUID, Decimal]]:
    if not participant_splits:
        raise InvalidParticipantsError()

    cent = Decimal('0.01')

    splits = []

    for index, (participant_id, percentage) in enumerate(participant_splits):
        amount = ((total_amount * percentage) / 100).quantize(cent, rounding=ROUND_DOWN)
        splits.append((participant_id, amount))

    rounded_sum = sum(amount for _, amount in splits)

    remainder = total_amount - rounded_sum
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

    if isinstance(expense_data, EqualExpenseCreateRequest):
        amount_split = calculate_equal_splits(expense_data.total_amount, participant_ids)

    elif isinstance(expense_data, ExactExpenseCreateRequest):

        participant_splits = [(participant.user_id, participant.amount) for participant in expense_data.participants]
        amount_split = calculate_exact_splits(expense_data.total_amount, participant_splits)

    elif isinstance(expense_data, PercentageExpenseCreateRequest):

        participant_splits = [(participant.user_id, participant.percentage) for participant in expense_data.participants]
        amount_split = calculate_percentage_splits(expense_data.total_amount, participant_splits)

    else:
        raise ValueError('Unsupported expense split type')

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

def get_group_expenses(db: Session, current_user: User, group_id: uuid.UUID, limit: int | None = None, offset: int | None = None, payer_id: uuid.UUID | None = None, date_from: datetime | None = None) -> list[Expense]:
    group = get_group_by_raw_id(db, group_id)
    if group is None:
        raise GroupNotFound()
    current_member = get_group_member(db, group_id, current_user.id)
    if current_member is None:
        raise PermissionDeniedError()

    stmt = (select(Expense).where(Expense.group_id == group_id))

    if payer_id is not None:
        stmt = stmt.where(Expense.payer_id == payer_id)

    if date_from is not None:
        stmt = stmt.where(Expense.expense_date >= date_from)

    stmt = stmt.options(selectinload(Expense.splits)).order_by(Expense.expense_date.desc(), Expense.created_at.desc())

    if limit is not None:
        stmt = stmt.limit(limit)
    if offset is not None:
        stmt = stmt.offset(offset)

    expenses = cast(list[Expense], db.scalars(stmt).all())
    return expenses

def get_expense_by_id(db: Session, current_user: User, expense_id: uuid.UUID) -> Expense:
    stmt = select(Expense).where(Expense.id==expense_id).options(selectinload(Expense.splits))
    expense = db.scalar(stmt)

    if expense is None:
        raise ExpenseNotFound()
    current_member = get_group_member(db, expense.group_id, current_user.id)
    if current_member is None:
        raise PermissionDeniedError()
    return expense

def update_expense(db: Session, current_user: User, expense_id: uuid.UUID, expense_data: ExpenseUpdateRequest) -> Expense:
    expense = get_expense_by_id(db, current_user, expense_id)

    if expense.created_by != current_user.id:
        raise PermissionDeniedError()

    is_metadata_update = expense_data.participants is None
    amount_split = None

    if is_metadata_update:
        if expense_data.payer_id is not None:
            payer_id_validation = get_group_member(db, expense.group_id, expense_data.payer_id)
            if payer_id_validation is None:
                raise InvalidPayerError()

        for field, value in expense_data.model_dump(exclude_unset=True).items():
            setattr(expense, field, value)

    else:

        participant_ids = [participant.user_id for participant in expense_data.participants]

        payer_id = expense_data.payer_id or expense.payer_id
        validate_expense_memberships(db, current_user, expense.group_id, payer_id, participant_ids)

        if expense_data.split_type == 'equal':
            amount_split = calculate_equal_splits(expense_data.total_amount, participant_ids)
        elif expense_data.split_type == 'exact':
            participant_splits = [(participant.user_id, participant.amount) for participant in expense_data.participants]
            amount_split = calculate_exact_splits(expense_data.total_amount, participant_splits)
        elif expense_data.split_type == 'percentage':
            participant_splits = [(participant.user_id, participant.percentage) for participant in expense_data.participants]
            amount_split = calculate_percentage_splits(expense_data.total_amount, participant_splits)
        else:
            raise ValueError('Unsupported expense split type')

        update_data_without_participants = expense_data.model_dump(exclude_unset=True, exclude={'participants'})
        for field, value in update_data_without_participants.items():
            setattr(expense, field, value)

    try:
        if amount_split is not None:
            stmt = delete(ExpenseSplit).where(ExpenseSplit.expense_id == expense_id)
            db.execute(stmt)

            new_splits = [
                ExpenseSplit(
                    expense_id=expense_id,
                    user_id=participant_id,
                    amount_owed=amount
                )
                for participant_id, amount in amount_split
            ]
            db.add_all(new_splits)
        db.commit()
        db.refresh(expense)

        stmt = (select(Expense).where(Expense.id == expense_id).options(selectinload(Expense.splits)))
        updated_expense = db.scalar(stmt)

        if updated_expense is None:
            raise ExpenseNotFound()
        return updated_expense

    except IntegrityError:
        db.rollback()
        raise

def delete_expense(db: Session, current_user: User, expense_id: uuid.UUID) -> None:
    expense = get_expense_by_id(db, current_user, expense_id)

    if expense.created_by != current_user.id:
        raise PermissionDeniedError()

    try:
        stmt = delete(ExpenseSplit).where(ExpenseSplit.expense_id == expense_id)
        db.execute(stmt)

        db.delete(expense)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise