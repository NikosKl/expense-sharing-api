import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import User, Settlement
from app.schemas.settlement import SettlementCreateRequest
from app.services.exceptions import GroupNotFound, PermissionDeniedError, InvalidPayerError, InvalidReceiverError
from app.services.group_member_service import get_group_member
from app.services.group_service import get_group_by_raw_id

def validate_settlement_memberships(db: Session, current_user: User, group_id: uuid.UUID, payer_id: uuid.UUID, receiver_id: uuid.UUID) -> None:
    group = get_group_by_raw_id(db, group_id)
    if group is None:
        raise GroupNotFound()
    current_member = get_group_member(db, group_id, current_user.id)
    if current_member is None:
        raise PermissionDeniedError()
    payer = get_group_member(db, group_id, payer_id)
    if payer is None:
        raise InvalidPayerError()
    receiver = get_group_member(db, group_id, receiver_id)
    if receiver is None:
        raise InvalidReceiverError()

def create_settlement(db: Session, current_user: User, group_id: uuid.UUID, settlement_data: SettlementCreateRequest) -> Settlement:
    validate_settlement_memberships(db, current_user, group_id, settlement_data.payer_id, settlement_data.receiver_id)

    settlement = Settlement(
        group_id=group_id,
        payer_id=settlement_data.payer_id,
        receiver_id=settlement_data.receiver_id,
        amount=settlement_data.amount,
        note=settlement_data.note,
        settled_at=settlement_data.settled_at
    )

    try:
        db.add(settlement)
        db.commit()
        db.refresh(settlement)
        return settlement
    except IntegrityError:
        db.rollback()
        raise
