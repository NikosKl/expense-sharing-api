import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.settlement import SettlementResponse, SettlementCreateRequest
from app.services.exceptions import GroupNotFound, PermissionDeniedError, InvalidPayerError, InvalidReceiverError, \
    InvalidSettlementAmountError
from app.services.settlement_service import create_settlement

router = APIRouter(prefix='/groups', tags=['settlements'])

@router.post('/{group_id}/settlements', response_model=SettlementResponse)
def create_group_settlement(group_id: uuid.UUID, settlement_request: SettlementCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        settlement = create_settlement(db, current_user, group_id, settlement_request)
        return settlement
    except GroupNotFound:
        raise HTTPException(status_code=404, detail='Group not found')
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail='You do not have permission to perform this action')
    except InvalidPayerError:
        raise HTTPException(status_code=400, detail='Payer must be a member of the group')
    except InvalidReceiverError:
        raise HTTPException(status_code=400, detail='Receiver must be a member of the group')
    except InvalidSettlementAmountError:
        raise HTTPException(status_code=400, detail='Settlement amount exceeds the allowed outstanding balance')