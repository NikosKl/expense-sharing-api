import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.audit_log import AuditLogResponse
from app.services.audit_log_service import get_group_audit_logs
from app.services.exceptions import GroupNotFound, PermissionDeniedError

router = APIRouter(prefix="/groups", tags=["audit-logs"])

@router.get("/{group_id}/audit-logs", response_model=list[AuditLogResponse])
def list_group_audit_logs(
        group_id: uuid.UUID,
        limit: int = Query(20, gt=0),
        offset: int = Query(0, ge=0),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    try:
        audit_logs = get_group_audit_logs(db, current_user, group_id, limit, offset)
        return audit_logs
    except GroupNotFound:
        raise HTTPException(status_code=404, detail="Group not found")
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")
