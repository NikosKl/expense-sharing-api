from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session
from app.core.security import decode_token
from app.db.session import get_db
from app.models import User
from app.services.user_service import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid token',
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id = payload.get('sub')
    except InvalidTokenError:
        raise credentials_exception

    if user_id is None:
        raise credentials_exception

    try:
        user_id = UUID(user_id)
    except ValueError:
        raise credentials_exception

    user = get_user_by_id(db, user_id)

    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=403, detail='Inactive user')

    return user

