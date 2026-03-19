from pydantic import BaseModel, EmailStr, field_validator

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str | None = None

    @field_validator('password')
    @classmethod
    def check_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return value

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int | None = None