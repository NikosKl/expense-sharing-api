from __future__ import annotations
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, String, Numeric, DateTime, Boolean, func, CheckConstraint

from app.db.base import Base

from sqlalchemy.orm import mapped_column, Mapped, relationship

if TYPE_CHECKING:
    from app.models.recurring_expense_splits import RecurringExpenseSplit


class RecurringExpense(Base):
    __tablename__ = 'recurring_expenses'
    __table_args__ = (
        CheckConstraint("split_type in ('equal', 'exact', 'percentage')", name='chk_recurring_expenses_split_type'),
        CheckConstraint("total_amount > 0", name='chk_recurring_expenses_total_amount'),
        CheckConstraint("frequency in ('daily', 'weekly', 'monthly')", name='chk_recurring_expenses_frequency'),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('groups.id'), index=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)
    payer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    split_type: Mapped[str] = mapped_column(String(20), nullable=False)
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    splits: Mapped[list[RecurringExpenseSplit]] = relationship(
        back_populates='recurring_expense',
        cascade='all, delete-orphan',
        passive_deletes=True)