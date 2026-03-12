"""Authentication and authorization tests"""

import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
from sqlalchemy.orm import Session
from src.models import User
from src.services.auth import AuthService
from src.middleware.auth import create_access_token, verify_token
from src.config import get_settings


@pytest.fixture
def auth_service(db_session):
    """Provide AuthService instance"""
    return AuthService()


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        user_id="test_user",
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        password_hash="hashed_password",
        role="analyst",
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestUserAuthentication:
    """Test user login and authentication flow"""

    def test_register_user_success(self, auth_service, db_session):
        """Test successful user registration"""
        result = auth_service.register_user(
            db=db_session,
            username="newuser",
            email="new@example.com",
            password="secure_password_123",
            full_name="New User",
        )
        assert result is not None
        assert result.username == "newuser"
        assert result.email == "new@example.com"

    def test_register_user_duplicate_username(self, auth_service, db_session, test_user):
        """Test registration with duplicate username"""
        with pytest.raises(ValueError, match="Username already exists"):
            auth_service.register_user(
                db=db_session,
                username="testuser",
                email="other@example.com",
                password="password123",
                full_name="Other User",
            )

    def test_login_success(self, auth_service, db_session, test_user):
        """Test successful login"""
        # First, manually set a proper hash
        auth_service.hash_password("correct_password")
        test_user.password_hash = auth_service.hash_password("correct_password")
        db_session.commit()

        user = auth_service.authenticate_user(
            db=db_session, username="testuser", password="correct_password"
        )
        assert user is not None
        assert user.user_id == "test_user"

    def test_login_invalid_password(self, auth_service, db_session, test_user):
        """Test login with wrong password"""
        test_user.password_hash = auth_service.hash_password("correct_password")
        db_session.commit()

        user = auth_service.authenticate_user(
            db=db_session, username="testuser", password="wrong_password"
        )
        assert user is None

    def test_login_nonexistent_user(self, auth_service, db_session):
        """Test login with non-existent user"""
        user = auth_service.authenticate_user(
            db=db_session, username="nonexistent", password="password"
        )
        assert user is None


class TestTokenGeneration:
    """Test JWT token generation and validation"""

    @freeze_time("2024-01-01 12:00:00")
    def test_create_access_token(self):
        """Test access token creation"""
        settings = get_settings()
        user_id = "test_user"

        token = create_access_token(user_id=user_id)
        assert token is not None
        assert isinstance(token, str)

    @freeze_time("2024-01-01 12:00:00")
    def test_verify_valid_token(self):
        """Test verifying a valid token"""
        user_id = "test_user"
        token = create_access_token(user_id=user_id)

        decoded = verify_token(token)
        assert decoded is not None
        assert decoded.get("sub") == user_id

    def test_verify_expired_token(self):
        """Test verifying an expired token"""
        with freeze_time("2024-01-01 12:00:00"):
            token = create_access_token(user_id="test_user")

        with freeze_time("2024-01-02 13:00:00"):  # Next day
            decoded = verify_token(token)
            assert decoded is None  # Should be invalid

    def test_verify_invalid_token(self):
        """Test verifying invalid token"""
        decoded = verify_token("invalid.token.here")
        assert decoded is None

    def test_verify_malformed_token(self):
        """Test verifying malformed token"""
        decoded = verify_token("not-a-jwt-token")
        assert decoded is None
