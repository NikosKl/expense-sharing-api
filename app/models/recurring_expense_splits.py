from __future__ import annotations
from typing import TYPE_CHECKING
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from sqlalchemy import UUID, ForeignKey, Numeric, DateTime, func, UniqueConstraint, CheckConstraint

if TYPE_CHECKING:
    from app.models.recurring_expense import RecurringExpense


class RecurringExpenseSplit(Base):
    __tablename__ = 'recurring_expense_splits'
    __table_args__ = (
        CheckConstraint('amount_owed > 0', name='chk_recurring_expense_splits_positive'),
        UniqueConstraint('user_id', 'recurring_expense_id', name='uniq_recurring_expense_splits_user')
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recurring_expense_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('recurring_expenses.id', ondelete='CASCADE'), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)
    amount_owed: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    recurring_expense: Mapped[RecurringExpense] = relationship(back_populates='splits')