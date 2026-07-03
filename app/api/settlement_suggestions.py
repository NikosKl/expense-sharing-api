import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.settlement import SettlementSuggestionsResponse
from app.services.exceptions import GroupNotFound, PermissionDeniedError
from app.services.settlement_suggestion_service import get_settlement_suggestions

router = APIRouter(prefix="/groups", tags=["settlement-suggestions"])

@router.get("/{group_id}/settlement-suggestions", response_model=SettlementSuggestionsResponse)
def settlement_suggestions(group_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        suggestions = get_settlement_suggestions(db, current_user, group_id)
        return suggestions
    except GroupNotFound:
        raise HTTPException(status_code=404, detail="Group not found")
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")

