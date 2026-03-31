from pydantic import EmailStr
from sqlalchemy.orm import Session
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models import User
from app.services.user_service import get_user_by_email, get_user_by_username
from app.services.exceptions import UserAlreadyExistsError, InactiveUserError, InvalidCredentialsError

def register_user(db: Session, email: EmailStr, username: str, password: str, full_name: str | None) -> User:
    existing_email = get_user_by_email(db, email)
    if existing_email is not None:
        raise UserAlreadyExistsError('Email already registered')
    existing_username = get_user_by_username(db, username)
    if existing_username is not None:
        raise UserAlreadyExistsError('Username already registered')

    normalized_email = email.lower().strip()
    normalized_username = username.lower().strip()

    user = User(
        email=normalized_email,
        username=normalized_username,
        hashed_password=get_password_hash(password),
        full_name=full_name,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, email: EmailStr, password: str) -> User:
    user = get_user_by_email(db, email)

    if user is None:
        raise InvalidCredentialsError('Invalid credentials')
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError('Invalid credentials')
    if not user.is_active:
        raise InactiveUserError('Inactive user')
    return user

def create_access_token_for_user(user: User) -> str:
    return create_access_token(data={'sub': str(user.id)})

