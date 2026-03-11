"""Pytest configuration and shared fixtures"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.main import create_app
from src.database import Base
from src.dependencies import get_db


@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine (in-memory SQLite)"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create fresh test database session for each test"""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    db = SessionLocal()
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    
    yield db
    
    db.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_client(test_db_session):
    """Create test FastAPI client"""
    app = create_app()
    
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
