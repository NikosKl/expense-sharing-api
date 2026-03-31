from datetime import datetime
from decimal import Decimal
from sqlalchemy import UUID, String, ForeignKey, DateTime, func, Numeric, CheckConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship
import uuid
from app.db.base import Base
from app.models import ExpenseSplit


class Expense(Base):
    __tablename__ = 'expenses'
    __table_args__ = (CheckConstraint(
        "split_type in ('equal')", name='chk_expenses_split_type'),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('groups.id'), index=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)
    payer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    split_type: Mapped[str] = mapped_column(String(20), nullable=False, default='equal')
    expense_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    splits: Mapped[list["ExpenseSplit"]] = relationship(back_populates="expense")