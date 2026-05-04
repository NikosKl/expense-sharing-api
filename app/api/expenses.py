import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.expense import ExpenseResponse
from app.services.exceptions import ExpenseNotFound, PermissionDeniedError
from app.services.expense_service import get_expense_by_id

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.get('/{expense_id}', response_model=ExpenseResponse)
def get_expense(expense_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        expense = get_expense_by_id(db, current_user, expense_id)
        return expense
    except ExpenseNotFound:
        raise HTTPException(status_code=404, detail="Expense not found")
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")