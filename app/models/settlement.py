import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import UUID, ForeignKey, Numeric, String, DateTime, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class Settlement(Base):
    __tablename__ = 'settlements'
    __table_args__ = (
        CheckConstraint('amount > 0', name='ck_settlements_amount_positive'),
        CheckConstraint('payer_id != receiver_id', name='ck_settlements_payer_not_receiver'),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('groups.id'), index=True, nullable=False)
    payer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)
    receiver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    note: Mapped[str|None] = mapped_column(String(255), nullable = True)
    settled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
