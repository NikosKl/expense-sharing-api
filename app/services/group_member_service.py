import uuid
from typing import cast
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import GroupMember, User
from app.services.audit_log_service import create_audit_log
from app.services.exceptions import GroupNotFound, PermissionDeniedError, UserNotFound, GroupMemberAlreadyExists, \
    CannotRemoveSelfFromGroupError
from app.services.group_service import get_group_by_id, get_group_by_raw_id
from app.services.user_service import get_user_by_id

def add_member_to_group(db: Session, current_user: User, group_id: uuid.UUID, user_to_add: uuid.UUID) -> GroupMember:

    group = get_group_by_id(db, current_user, group_id)
    if group is None:
        raise GroupNotFound()
    current_member = get_group_member(db, group_id, current_user.id)
    if current_member is None:
        raise PermissionDeniedError()
    if current_member.role != 'owner':
        raise PermissionDeniedError()
    user = get_user_by_id(db, user_to_add)
    if user is None:
        raise UserNotFound()
    existing_member = get_group_member(db, group_id, user_to_add)
    if existing_member is not None:
        raise GroupMemberAlreadyExists()

    group_member = GroupMember(
        group_id=group_id,
        user_id=user_to_add,
        role="member"
    )

    try:
        db.add(group_member)
        db.flush()

        create_audit_log(
            db=db,
            group_id=group_id,
            performed_by_id=current_user.id,
            action='group_member.added',
            target_type='group_member',
            target_id=group_member.id,
            details={
                'added_user_id': str(user_to_add),
                'role': group_member.role
            }
        )
        db.commit()
        db.refresh(group_member)
        return group_member
    except IntegrityError:
        db.rollback()
        raise

def get_group_member(db: Session, group_id: uuid.UUID, user_id: uuid.UUID) -> GroupMember | None:
    stmt = select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
    group_member = db.scalar(stmt)
    return group_member

def get_group_members(db: Session, current_user: User, group_id: uuid.UUID) -> list[GroupMember]:
    group = get_group_by_raw_id(db, group_id)
    if group is None:
        raise GroupNotFound()
    current_member = get_group_member(db, group_id, current_user.id)
    if current_member is None:
        raise PermissionDeniedError()

    stmt = select(GroupMember).where(GroupMember.group_id == group_id)

    group_members = cast(list[GroupMember], db.scalars(stmt).all())
    return group_members

def remove_group_member(db: Session, current_user: User, group_id: uuid.UUID, user_to_remove: uuid.UUID) ->  None:
    group = get_group_by_id(db, current_user, group_id)
    if group is None:
        raise GroupNotFound()
    current_membership = get_group_member(db, group_id, current_user.id)
    if current_membership is None:
        raise PermissionDeniedError()
    if current_membership.role != 'owner':
        raise PermissionDeniedError()
    if current_membership.user_id == user_to_remove:
        raise CannotRemoveSelfFromGroupError()
    stmt = select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user_to_remove)
    member = db.scalar(stmt)
    if member is None:
        raise UserNotFound()

    try:
        create_audit_log(
            db=db,
            group_id=group_id,
            performed_by_id=current_user.id,
            action='group_member.removed',
            target_type='group_member',
            target_id=member.id,
            details={
                'removed_user_id': str(user_to_remove),
                'role': member.role
            }
        )

        db.delete(member)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise