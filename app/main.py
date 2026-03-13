from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

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
