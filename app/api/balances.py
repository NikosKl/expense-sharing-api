import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.balance import GroupBalancesResponse
from app.services.balance_service import get_group_balances
from app.services.exceptions import GroupNotFound, PermissionDeniedError

router = APIRouter(prefix='/groups', tags=['balances'])

@router.get('/{group_id}/balances', response_model=GroupBalancesResponse)
def get_balances(group_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        group_balance = get_group_balances(db, current_user, group_id)
        return group_balance
    except GroupNotFound:
        raise HTTPException(status_code=404, detail='Group not found')
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail='You do not have permission to perform this action')