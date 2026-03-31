import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.group import GroupResponse, GroupCreateRequest
from app.schemas.group_member import GroupMemberCreateRequest, GroupMemberResponse
from app.services.group_member_service import add_member_to_group, get_group_members, remove_group_member
from app.services.exceptions import CannotRemoveSelfFromGroupError, GroupNotFound, PermissionDeniedError, UserNotFound, GroupMemberAlreadyExists
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

@router.post('/{group_id}/members', response_model=GroupMemberResponse)
def add_membership(group_id: uuid.UUID, group_request: GroupMemberCreateRequest , db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        member = add_member_to_group(db, current_user, group_id, group_request.user_id)
        return member
    except GroupNotFound:
        raise HTTPException(status_code=404, detail="Group not found")
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")
    except UserNotFound:
        raise HTTPException(status_code=404, detail="User not found")
    except GroupMemberAlreadyExists:
        raise HTTPException(status_code=409, detail="User is already a member of the group")

@router.get('/{group_id}/members', response_model=list[GroupMemberResponse])
def get_all_members_from_group(group_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        group_members = get_group_members(db, current_user, group_id)
        return group_members
    except GroupNotFound:
        raise HTTPException(status_code=404, detail="Group not found")
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")

@router.delete('/{group_id}/members/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_member_from_group(group_id: uuid.UUID, user_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        remove_group_member(db, current_user, group_id, user_id)
    except GroupNotFound:
        raise HTTPException(status_code=404, detail="Group not found")
    except UserNotFound:
        raise HTTPException(status_code=404, detail="User not found")
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")
    except CannotRemoveSelfFromGroupError:
        raise HTTPException(status_code=403, detail="You are not allowed to perform this action")