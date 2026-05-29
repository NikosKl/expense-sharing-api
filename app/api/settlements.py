import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.services.exceptions import SettlementNotFound, GroupNotFound, PermissionDeniedError
from app.services.settlement_service import delete_settlement

router = APIRouter(prefix="/settlements", tags=["settlements"])

@router.delete('/{settlement_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_settlement(settlement_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        delete_settlement(db, current_user, settlement_id)
    except SettlementNotFound:
        raise HTTPException(status_code=404, detail='Settlement not found')
    except GroupNotFound:
        raise HTTPException(status_code=404, detail='Group not found')
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail='You do not have permission to perform this action')
