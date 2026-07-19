import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User, RecurringExpense, RecurringExpenseSplit
from app.schemas.recurring_expense import RecurringExpenseCreateRequest, ExactRecurringExpenseCreateRequest, \
    EqualRecurringExpenseCreateRequest, PercentageRecurringExpenseCreateRequest
from app.services.audit_log_service import create_audit_log
from app.services.expense_service import validate_expense_memberships, calculate_equal_splits, calculate_exact_splits, \
    calculate_percentage_splits


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