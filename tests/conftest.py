import os
from dotenv import load_dotenv

load_dotenv()

os.environ['ENVIRONMENT'] = 'testing'
os.environ['JWT_SECRET_KEY'] = 'very_long_test_secret_key_32_bytes'
TEST_DATABASE_URL = os.environ.get('TEST_DATABASE_URL')

if not TEST_DATABASE_URL:
    raise RuntimeError('TEST_DATABASE_URL is not set')

os.environ['DATABASE_URL'] = TEST_DATABASE_URL

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient
import app.models
from app.db.base import Base
from app.db.session import get_db
from app.main import app

engine = create_engine(TEST_DATABASE_URL)
TestSession = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False)

@pytest.fixture(scope='session', autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def db_session():
    connection = engine.connect()
    outer_transaction = connection.begin()

    session = TestSession(bind=connection, join_transaction_mode='create_savepoint')

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()

@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)