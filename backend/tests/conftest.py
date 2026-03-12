"""Pytest configuration and shared fixtures"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import Base
from src.dependencies import get_db
from src.main import create_app
from src.models import User


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


# User fixtures for role-based tests
@pytest.fixture
def admin_user(test_db_session):
    """Create an admin test user"""
    user = User(
        user_id="admin_user",
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        password_hash="hashed_password",
        role="admin",
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


@pytest.fixture
def analyst_user(test_db_session):
    """Create an analyst test user"""
    user = User(
        user_id="analyst_user",
        username="analyst",
        email="analyst@example.com",
        full_name="Analyst User",
        password_hash="hashed_password",
        role="analyst",
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


@pytest.fixture
def auditor_user(test_db_session):
    """Create an auditor test user"""
    user = User(
        user_id="auditor_user",
        username="auditor",
        email="auditor@example.com",
        full_name="Auditor User",
        password_hash="hashed_password",
        role="auditor",
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


@pytest.fixture
def guest_user(test_db_session):
    """Create a guest test user"""
    user = User(
        user_id="guest_user",
        username="guest",
        email="guest@example.com",
        full_name="Guest User",
        password_hash="hashed_password",
        role="guest",
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


# Alias for consistency across tests
@pytest.fixture
def db_session(test_db_session):
    """Alias for test_db_session"""
    return test_db_session


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
