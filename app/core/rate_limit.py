from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi import Request
from starlette.responses import JSONResponse

from app.core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.environment != 'testing' and settings.rate_limit_enabled
)

async def rate_limit_exceeded_handler(
        request: Request,
        exc: RateLimitExceeded,
) -> JSONResponse:
    return JSONResponse(
        status_code=429, content={'detail': 'Rate limit exceeded. Please try again later.'}
    )