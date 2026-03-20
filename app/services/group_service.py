import uuid
from typing import cast
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import Group, User, GroupMember
from app.schemas.group import GroupCreateRequest

def create_group(db: Session, current_user: User, group_data: GroupCreateRequest) -> Group:
    group = Group(
        name=group_data.name,
        description=group_data.description,
        created_by=current_user.id
    )

    db.add(group)
    db.flush()

    group_member = GroupMember(
        group_id=group.id,
        user_id=current_user.id,
        role='owner'
    )
    try:
        db.add(group_member)
        db.commit()
        db.refresh(group)
        return group
    except IntegrityError as err:
        db.rollback()
        raise err

def get_groups_for_user(db: Session, current_user: User) -> list[Group]:

    stmt = select(Group).join(GroupMember).where(GroupMember.user_id == current_user.id)

    groups = cast(list[Group], db.scalars(stmt).all())
    return groups

def get_group_by_id(db: Session, current_user: User, group_id: uuid.UUID) -> Group | None:
    stmt = select(Group).join(GroupMember).where(Group.id == group_id, GroupMember.user_id == current_user.id)
    group = db.scalar(stmt)
    return group
