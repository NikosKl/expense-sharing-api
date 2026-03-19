from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import TypeAdapter, EmailStr, ValidationError
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import register_user, UserAlreadyExistsError, authenticate_user, InvalidCredentialsError, \
    create_access_token_for_user, InactiveUserError

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
def register(user: RegisterRequest, db: Session = Depends(get_db)):
    try:
        created_user = register_user(
            db,
            email=user.email,
            username=user.username,
            password=user.password,
            full_name=user.full_name)
    except UserAlreadyExistsError:
        raise HTTPException(status_code=409, detail="User already exists")
    return created_user

@router.post("/login",
             response_model=TokenResponse,
             description="Authenticate a user and return an access token.\n\n"
        "Note: in the OAuth2 form, the `username` field must contain the user's email address.")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        email = TypeAdapter(EmailStr).validate_python(form_data.username)
        authenticated_user = authenticate_user(
            db,
            email=email,
            password=form_data.password)
    except ValidationError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except InactiveUserError:
        raise HTTPException(status_code=403, detail="Inactive user")
    access_token = create_access_token_for_user(authenticated_user)
    return {'access_token': access_token, 'token_type': 'bearer'}

@router.get("/me", response_model=UserResponse)
def read_user(current_user: User = Depends(get_current_user)):
    return current_user

