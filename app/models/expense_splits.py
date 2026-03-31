from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from sqlalchemy import UUID, ForeignKey, Numeric, CheckConstraint, UniqueConstraint, func, DateTime
from sqlalchemy.orm import mapped_column, Mapped, relationship
import uuid
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.expense import Expense

class ExpenseSplit(Base):
    __tablename__ = "expense_splits"
    __table_args__ = (
        CheckConstraint("amount_owed > 0", name="ck_expense_splits_amount_positive"),
        UniqueConstraint("expense_id", "user_id", name="uniq_expense_splits_expense_user"))

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expense_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('expenses.id'), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)
    amount_owed: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    expense: Mapped["Expense"] = relationship(back_populates="splits")
