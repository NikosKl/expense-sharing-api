import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.group import GroupResponse, GroupCreateRequest
from app.services.group_service import create_group, get_group_by_id, get_groups_for_user

router = APIRouter(prefix="/groups", tags=["groups"])

@router.post("/", response_model=GroupResponse)
def create_new_group(group_request: GroupCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = create_group(db, current_user, group_request)
    return group

@router.get('/', response_model=list[GroupResponse])
def get_all_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    groups = get_groups_for_user(db, current_user)
    return groups

@router.get("/{group_id}", response_model=GroupResponse)
def get_group(group_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = get_group_by_id(db, current_user, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return group