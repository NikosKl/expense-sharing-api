import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.settlement import SettlementResponse, SettlementUpdateRequest
from app.services.exceptions import SettlementNotFound, GroupNotFound, PermissionDeniedError, InvalidReceiverError, \
    InvalidSettlementAmountError, InvalidSettlementParticipantError
from app.services.settlement_service import delete_settlement, update_settlement

router = APIRouter(prefix="/settlements", tags=["settlements"])

@router.patch("/{settlement_id}", response_model=SettlementResponse)
def update_existing_settlement(settlement_id: uuid.UUID, settlement_data: SettlementUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        updated_settlement = update_settlement(db, current_user, settlement_id, settlement_data)
        return updated_settlement
    except SettlementNotFound:
        raise HTTPException(status_code=404, detail='Settlement not found')
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail='You do not have permission to perform this action')
    except InvalidReceiverError:
        raise HTTPException(status_code=400, detail='Receiver must be a member of the group')
    except InvalidSettlementParticipantError:
        raise HTTPException(status_code=400, detail='Payer and receiver cannot be the same')
    except InvalidSettlementAmountError:
        raise HTTPException(status_code=400, detail='Settlement amount exceeds the allowed outstanding balance')

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
