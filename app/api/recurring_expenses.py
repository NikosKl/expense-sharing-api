import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.services.exceptions import RecurringExpenseNotFound, PermissionDeniedError
from app.services.recurring_expense_service import cancel_recurring_expense

router = APIRouter(prefix="/recurring-expenses", tags=["recurring-expenses"])

@router.delete('/{recurring_expense_id}', status_code=status.HTTP_204_NO_CONTENT)
def cancel_existing_recurring_expense(
        recurring_expense_id: uuid.UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):

    try:
        cancel_recurring_expense(db, current_user, recurring_expense_id)
    except RecurringExpenseNotFound:
        raise HTTPException(status_code=404, detail="Recurring expense not found")
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")