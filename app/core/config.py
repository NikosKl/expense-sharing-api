from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = Field(default='Expense Sharing API', alias='APP_NAME')
    app_version: str = Field(default='1.0', alias='APP_VERSION')
    environment: Literal['development', 'testing', 'production'] = Field(default='development', alias='ENVIRONMENT')

    database_url: str = Field(..., alias='DATABASE_URL')
    jwt_secret_key: str = Field(..., alias='JWT_SECRET_KEY')
    jwt_algorithm: str = Field(default='HS256', alias='JWT_ALGORITHM')
    access_token_expire_minutes: int = Field(default=30, alias='ACCESS_TOKEN_EXPIRE_MINUTES', gt=0)

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()

