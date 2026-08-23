import uuid
from typing import cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, User, GroupMember
from app.services.exceptions import GroupNotFound, PermissionDeniedError
from app.services.group_service import get_group_by_raw_id


def create_audit_log(
        db: Session,
        group_id: uuid.UUID,
        performed_by_id: uuid.UUID,
        action: str,
        target_type: str,
        target_id: uuid.UUID,
        details: dict | None = None) -> AuditLog:

    audit_log = AuditLog(
        group_id=group_id,
        performed_by_id=performed_by_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details
    )

    db.add(audit_log)
    return audit_log

def get_group_audit_logs(db: Session, current_user: User, group_id: uuid.UUID, limit: int | None, offset: int | None) -> list[AuditLog]:
    group = get_group_by_raw_id(db, group_id)
    if group is None:
        raise GroupNotFound()

    stmt = select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id)
    current_member = db.scalar(stmt)

    if current_member is None:
        raise PermissionDeniedError()

    stmt = select(AuditLog).where(AuditLog.group_id == group_id).order_by(AuditLog.created_at.desc())

    if limit is not None:
        stmt = stmt.limit(limit)
    if offset is not None:
        stmt = stmt.offset(offset)

    audit_logs = cast(list[AuditLog], db.scalars(stmt).all())
    return audit_logs