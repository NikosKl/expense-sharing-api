import uuid
from datetime import datetime
from sqlalchemy import UUID, ForeignKey, String, DateTime, func, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import mapped_column, Mapped
from app.db.base import Base

class GroupMember(Base):
    __tablename__ = "group_members"
    __table_args__ = (
        CheckConstraint(
            "role IN ('owner', 'member')",
            name='ck_group_member_role'),
        UniqueConstraint("group_id", "user_id", name="uniq_group_members_group_user"))

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("groups.id"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)