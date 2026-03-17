import uuid
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import User

def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    stmt = select(User).where(User.id == user_id)
    return db.scalar(stmt)

def get_user_by_email(db: Session, email: EmailStr) -> User | None:
    normalized_email = email.lower()
    stmt = select(User).where(User.email == normalized_email)
    return db.scalar(stmt)

def get_user_by_username(db: Session, username: str) -> User | None:
    normalized_username = username.lower()
    stmt = select(User).where(User.username == normalized_username)
    return db.scalar(stmt)
