import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.db.session import DBSession
from app.api.auth import router as auth_router
from app.api.groups import router as group_router
from app.api.group_expenses import router as group_expenses_router
from app.api.balances import router as balances_router
from app.api.group_settlements import router as group_settlements_router
from app.api.group_members import router as group_members_router
from app.api.expenses import router as expenses_router
from app.api.settlements import router as settlements_router
from app.api.settlement_suggestions import router as settlement_suggestions_router
from app.api.audit_logs import router as audit_logs_router
from app.api.group_recurring_expenses import router as group_recurring_expenses_router
from app.api.recurring_expenses import router as recurring_expenses_router
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = DBSession()
    try:
        db.execute(text('SELECT 1'))
        logger.info('Database connection successful')
    except Exception:
        logger.exception('Database connection failed')
        raise
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(auth_router)
app.include_router(group_router)
app.include_router(group_members_router)
app.include_router(group_expenses_router)
app.include_router(balances_router)
app.include_router(group_settlements_router)
app.include_router(expenses_router)
app.include_router(settlements_router)
app.include_router(settlement_suggestions_router)
app.include_router(audit_logs_router)
app.include_router(group_recurring_expenses_router)
app.include_router(recurring_expenses_router)

@app.get("/")
def read_root():
    return{
        'message': f'Welcome to {settings.app_name}',
        'version': settings.app_version,
        'environment': settings.environment,
    }

@app.get('/health')
def health():
    return {'status': 'ok'}
