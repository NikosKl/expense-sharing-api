import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.recurring_expense import RecurringExpenseResponse, RecurringExpenseCreateRequest
from app.services.exceptions import GroupNotFound, PermissionDeniedError, InvalidPayerError, InvalidParticipantsError, \
    InvalidExpenseSplitError
from app.services.recurring_expense_service import create_recurring_expense, get_group_recurring_expenses

router = APIRouter(prefix="/groups", tags=["recurring-expenses"])

@router.post('/{group_id}/recurring-expenses', response_model=RecurringExpenseResponse)
def create_new_recurring_expense(
        group_id: uuid.UUID,
        recurring_expense_request: RecurringExpenseCreateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):

    try:
        recurring_expense = create_recurring_expense(db, current_user, group_id, recurring_expense_request)
        return recurring_expense

    except GroupNotFound:
        raise HTTPException(status_code=404, detail="Group not found")
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")
    except InvalidPayerError:
        raise HTTPException(status_code=400, detail="Payer must be a member of the group")
    except InvalidParticipantsError:
        raise HTTPException(status_code=400, detail='All participants must be a member of the group')
    except InvalidExpenseSplitError:
        raise HTTPException(status_code=400, detail="Splits must sum up to total amount")

@router.get('/{group_id}/recurring-expenses', response_model=list[RecurringExpenseResponse])
def get_all_group_recurring_expenses(
        group_id: uuid.UUID,
        is_active: bool | None = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):

    try:
        recurring_expenses = get_group_recurring_expenses(db, current_user, group_id, is_active)
        return recurring_expenses

    except GroupNotFound:
        raise HTTPException(status_code=404, detail="Group not found")
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")