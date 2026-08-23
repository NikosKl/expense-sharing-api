from datetime import datetime
import uuid
from typing import cast

from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import User, RecurringExpense, RecurringExpenseSplit, Expense, ExpenseSplit
from app.schemas.recurring_expense import RecurringExpenseCreateRequest, ExactRecurringExpenseCreateRequest, \
    EqualRecurringExpenseCreateRequest, PercentageRecurringExpenseCreateRequest
from app.services.audit_log_service import create_audit_log
from app.services.exceptions import GroupNotFound, PermissionDeniedError, RecurringExpenseNotFound
from app.services.expense_service import validate_expense_memberships, calculate_equal_splits, calculate_exact_splits, \
    calculate_percentage_splits
from app.services.group_member_service import get_group_member
from app.services.group_service import get_group_by_raw_id


def create_recurring_expense(db: Session, current_user: User, group_id: uuid.UUID, recurring_expense_data: RecurringExpenseCreateRequest) -> RecurringExpense:

    participant_ids = [participant.user_id for participant in recurring_expense_data.participants]

    validate_expense_memberships(db, current_user, group_id, recurring_expense_data.payer_id, participant_ids)

    if isinstance(recurring_expense_data, EqualRecurringExpenseCreateRequest):
        amount_split = calculate_equal_splits(recurring_expense_data.total_amount, participant_ids)

    elif isinstance(recurring_expense_data, ExactRecurringExpenseCreateRequest):

        participant_splits = [(participant.user_id, participant.amount) for participant in recurring_expense_data.participants]
        amount_split = calculate_exact_splits(recurring_expense_data.total_amount, participant_splits)

    elif isinstance(recurring_expense_data, PercentageRecurringExpenseCreateRequest):

        participant_splits = [(participant.user_id, participant.percentage) for participant in recurring_expense_data.participants]
        amount_split = calculate_percentage_splits(recurring_expense_data.total_amount, participant_splits)

    else:
        raise ValueError('Unsupported recurring expense split type')

    recurring_expense = RecurringExpense(
        group_id=group_id,
        created_by=current_user.id,
        payer_id=recurring_expense_data.payer_id,
        title=recurring_expense_data.title,
        description=recurring_expense_data.description,
        total_amount=recurring_expense_data.total_amount,
        split_type=recurring_expense_data.split_type,
        frequency=recurring_expense_data.frequency,
        next_run_at=recurring_expense_data.next_run_at,
    )

    try:
        db.add(recurring_expense)
        db.flush()

        recurring_expense_split = [
            RecurringExpenseSplit(
                recurring_expense_id=recurring_expense.id,
                user_id=participant_id,
                amount_owed=amount
            )
            for participant_id, amount in amount_split
        ]

        db.add_all(recurring_expense_split)

        create_audit_log(
            db=db,
            group_id=group_id,
            performed_by_id=current_user.id,
            action='recurring_expense.created',
            target_type='recurring_expense',
            target_id=recurring_expense.id,
            details={
                'title': recurring_expense.title,
                'total_amount': str(recurring_expense.total_amount),
                'split_type': recurring_expense.split_type,
                'frequency': recurring_expense.frequency,
            }
        )

        db.commit()
        db.refresh(recurring_expense)
        return recurring_expense
    except IntegrityError:
        db.rollback()
        raise

def get_group_recurring_expenses(db: Session, current_user: User, group_id: uuid.UUID, is_active: bool | None = None) -> list[RecurringExpense]:
    group = get_group_by_raw_id(db, group_id)
    if not group:
        raise GroupNotFound()
    current_member = get_group_member(db, group_id, current_user.id)
    if not current_member:
        raise PermissionDeniedError()

    stmt = (select(RecurringExpense).where(RecurringExpense.group_id == group.id))

    if is_active is not None:
        stmt = stmt.where(RecurringExpense.is_active == is_active)

    stmt = stmt.options(selectinload(RecurringExpense.splits)).order_by(RecurringExpense.next_run_at.asc(), RecurringExpense.created_at.desc())

    recurring_expenses = cast(list[RecurringExpense], db.scalars(stmt).all())
    return recurring_expenses

def get_recurring_expense_by_id(db: Session, current_user: User, recurring_expense_id: uuid.UUID) -> RecurringExpense:
    stmt = select(RecurringExpense).where(RecurringExpense.id == recurring_expense_id).options(selectinload(RecurringExpense.splits))
    recurring_expense = db.scalar(stmt)

    if recurring_expense is None:
        raise RecurringExpenseNotFound()
    current_member = get_group_member(db, recurring_expense.group_id, current_user.id)
    if current_member is None:
        raise PermissionDeniedError()
    return recurring_expense

def cancel_recurring_expense(db: Session, current_user: User, recurring_expense_id: uuid.UUID) -> None:
    recurring_expense = get_recurring_expense_by_id(db, current_user, recurring_expense_id)

    if recurring_expense.created_by != current_user.id:
        raise PermissionDeniedError()

    try:
        recurring_expense.is_active = False

        create_audit_log(
            db=db,
            group_id=recurring_expense.group_id,
            performed_by_id=current_user.id,
            action='recurring_expense.canceled',
            target_type='recurring_expense',
            target_id=recurring_expense.id,
            details={
                'title': recurring_expense.title,
                'frequency': recurring_expense.frequency
            }
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

def calculate_next_run_at(current_next_run_at: datetime, frequency: str) -> datetime:
    if frequency == 'daily':
        return current_next_run_at + relativedelta(days=1)
    elif frequency == 'weekly':
        return current_next_run_at + relativedelta(weeks=1)
    elif frequency == 'monthly':
        return current_next_run_at + relativedelta(months=1)
    else:
        raise ValueError('Unsupported recurring expense frequency')


def process_due_recurring_expenses(db: Session, now: datetime) -> int:
    stmt = select(RecurringExpense).where(RecurringExpense.is_active.is_(True), RecurringExpense.next_run_at <= now).options(selectinload(RecurringExpense.splits))
    due_recurring_expenses = db.scalars(stmt).all()

    created_count = 0

    try:
        for recurring_expense in due_recurring_expenses:
            old_next_run_at = recurring_expense.next_run_at

            expense = Expense(
                group_id=recurring_expense.group_id,
                created_by=recurring_expense.created_by,
                payer_id=recurring_expense.payer_id,
                title=recurring_expense.title,
                description=recurring_expense.description,
                total_amount=recurring_expense.total_amount,
                split_type=recurring_expense.split_type,
                expense_date=old_next_run_at,
            )

            db.add(expense)
            db.flush()

            expense_split = [
                ExpenseSplit(
                    expense_id=expense.id,
                    user_id=recurring_split.user_id,
                    amount_owed=recurring_split.amount_owed,
                )
                for recurring_split in recurring_expense.splits
            ]

            db.add_all(expense_split)

            created_count += 1

            recurring_expense.next_run_at = calculate_next_run_at(recurring_expense.next_run_at, recurring_expense.frequency)

            create_audit_log(
                db=db,
                group_id=expense.group_id,
                performed_by_id=expense.created_by,
                action='recurring_expense.processed',
                target_type='recurring_expense',
                target_id=recurring_expense.id,
                details={
                    'expense_id': str(expense.id),
                    'title': expense.title,
                    'total_amount': str(expense.total_amount),
                    'split_type': expense.split_type,
                    'old_next_run_at': datetime.isoformat(old_next_run_at),
                    'new_next_run_at': datetime.isoformat(recurring_expense.next_run_at),
                }
            )
        db.commit()

        return created_count
    except IntegrityError:
        db.rollback()
        raise

