import uuid
from decimal import Decimal
from typing import cast
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import User, Settlement
from app.schemas.settlement import SettlementCreateRequest, SettlementUpdateRequest
from app.services.exceptions import GroupNotFound, PermissionDeniedError, InvalidPayerError, InvalidReceiverError, \
    InvalidSettlementAmountError, SettlementNotFound, InvalidSettlementParticipantError
from app.services.group_member_service import get_group_member
from app.services.group_service import get_group_by_raw_id
from app.services.helpers import calculate_group_balances


def validate_settlement_memberships(db: Session, current_user: User, group_id: uuid.UUID, payer_id: uuid.UUID, receiver_id: uuid.UUID) -> None:
    group = get_group_by_raw_id(db, group_id)
    if group is None:
        raise GroupNotFound()
    current_member = get_group_member(db, group_id, current_user.id)
    if current_member is None:
        raise PermissionDeniedError()
    if current_user.id != payer_id:
        raise PermissionDeniedError()
    payer = get_group_member(db, group_id, payer_id)
    if payer is None:
        raise InvalidPayerError()
    receiver = get_group_member(db, group_id, receiver_id)
    if receiver is None:
        raise InvalidReceiverError()

def create_settlement(db: Session, current_user: User, group_id: uuid.UUID, settlement_data: SettlementCreateRequest) -> Settlement:
    validate_settlement_memberships(db, current_user, group_id, settlement_data.payer_id, settlement_data.receiver_id)
    validate_settlement_against_balances(db, current_user, group_id, settlement_data.payer_id, settlement_data.receiver_id, settlement_data.amount)

    settlement = Settlement(
        group_id=group_id,
        created_by=current_user.id,
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

def get_group_settlements(db: Session, current_user: User, group_id: uuid.UUID, limit: int, offset: int, payer_id: uuid.UUID | None = None, receiver_id: uuid.UUID | None = None) -> list[Settlement]:
    validate_settlement_access(db, current_user, group_id)

    stmt = select(Settlement).where(Settlement.group_id == group_id)

    if payer_id is not None:
        stmt = stmt.where(Settlement.payer_id == payer_id)
    if receiver_id is not None:
        stmt = stmt.where(Settlement.receiver_id == receiver_id)

    stmt = stmt.order_by(Settlement.settled_at.desc(), Settlement.created_at.desc()).limit(limit).offset(offset)

    settlements = cast(list[Settlement], db.scalars(stmt).all())
    return settlements

def validate_settlement_access(db: Session, current_user: User, group_id: uuid.UUID) -> None:
    group = get_group_by_raw_id(db, group_id)
    if group is None:
        raise GroupNotFound()
    current_member = get_group_member(db, group_id, current_user.id)
    if current_member is None:
        raise PermissionDeniedError()

def validate_settlement_against_balances(db: Session, current_user: User, group_id: uuid.UUID, payer_id: uuid.UUID, receiver_id: uuid.UUID, amount: Decimal, exclude_settlement_id: uuid.UUID | None = None) -> None:
    group_balances = calculate_group_balances(db, current_user, group_id, exclude_settlement_id=exclude_settlement_id)

    payer_balance = group_balances.get(payer_id)
    receiver_balance = group_balances.get(receiver_id)

    if payer_balance is None or receiver_balance is None:
        raise InvalidSettlementAmountError()
    if payer_balance >= Decimal('0.00'):
        raise InvalidSettlementAmountError()
    if receiver_balance <= Decimal('0.00'):
        raise InvalidSettlementAmountError()

    max_amount = min(abs(payer_balance), receiver_balance)
    if amount > max_amount:
        raise InvalidSettlementAmountError()

def get_settlement_by_id(db: Session, current_user: User, settlement_id: uuid.UUID) -> Settlement:
    stmt = select(Settlement).where(Settlement.id == settlement_id)
    settlement = db.scalar(stmt)

    if settlement is None:
        raise SettlementNotFound()
    current_member = get_group_member(db, settlement.group_id, current_user.id)
    if current_member is None:
        raise PermissionDeniedError()
    return settlement

def delete_settlement(db: Session, current_user: User, settlement_id: uuid.UUID) -> None:
    stmt = select(Settlement).where(Settlement.id == settlement_id)
    settlement = db.scalar(stmt)

    if settlement is None:
        raise SettlementNotFound()

    validate_settlement_access(db, current_user, settlement.group_id)

    if settlement.created_by != current_user.id:
        raise PermissionDeniedError()

    try:
        db.delete(settlement)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

def update_settlement(db: Session, current_user: User, settlement_id: uuid.UUID, settlement_data: SettlementUpdateRequest) -> Settlement:
    settlement = get_settlement_by_id(db, current_user, settlement_id)

    if settlement.created_by != current_user.id:
        raise PermissionDeniedError()

    if settlement_data.receiver_id is not None:
        receiver_member = get_group_member(db, settlement.group_id, settlement_data.receiver_id)

        if receiver_member is None:
            raise InvalidReceiverError()

        if settlement_data.receiver_id == settlement.payer_id:
            raise InvalidSettlementParticipantError()

    new_receiver_id = settlement_data.receiver_id or settlement.receiver_id
    new_amount = settlement_data.amount or settlement.amount

    validate_settlement_against_balances(
        db,
        current_user,
        settlement.group_id,
        settlement.payer_id,
        new_receiver_id,
        new_amount,
        exclude_settlement_id=settlement.id
        )

    for field, value in settlement_data.model_dump(exclude_unset=True).items():
        setattr(settlement, field, value)

    try:
        db.commit()
        db.refresh(settlement)
        return settlement
    except IntegrityError:
        db.rollback()
        raise


