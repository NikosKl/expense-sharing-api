import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.expense import ExpenseResponse, ExpenseCreateRequest
from app.services.exceptions import GroupNotFound, PermissionDeniedError, InvalidPayerError, \
    InvalidParticipantsError
from app.services.expense_service import create_expense, get_group_expenses

router = APIRouter(prefix="/groups", tags=["groups"])

@router.post("/{group_id}/expenses", response_model=ExpenseResponse)
def create_new_expense(group_id: uuid.UUID, expense_request: ExpenseCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        expense = create_expense(db, current_user, group_id, expense_request)
        return expense
    except GroupNotFound:
        raise HTTPException(status_code=404, detail="Group not found")
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")
    except InvalidPayerError:
        raise HTTPException(status_code=400, detail="Payer must be a member of the group")
    except InvalidParticipantsError:
        raise HTTPException(status_code=400, detail="All participants must be member of the group")

@router.get('/{group_id}/expenses', response_model=List[ExpenseResponse])
def get_all_group_expenses(group_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        expenses = get_group_expenses(db, current_user, group_id)
        return expenses
    except GroupNotFound:
        raise HTTPException(status_code=404, detail="Group not found")
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")
