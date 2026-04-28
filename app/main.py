from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from app.core.config import settings
from app.db.session import DBSession
from app.api.auth import router as auth_router
from app.api.groups import router as group_router
from app.api.expenses import router as expenses_router
from app.api.balances import router as balances_router
from app.api.settlements import router as settlements_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = DBSession()
    try:
        db.execute(text('SELECT 1'))
        print('Database Connection Successful')
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

app.include_router(auth_router)
app.include_router(group_router)
app.include_router(expenses_router)
app.include_router(balances_router)
app.include_router(settlements_router)

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
