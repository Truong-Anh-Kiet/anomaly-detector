"""Integration tests for API endpoints - Phase 9"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.database import Base, get_db
from src.main import create_app
from src.models.category import Category
from src.models.user import RoleEnum, User

# Use in-memory SQLite for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override get_db dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """Provide FastAPI test client"""
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db():
    """Provide test database session"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db: Session):
    """Create a test user"""
    user = User(
        username="testuser",
        password_hash="hashed_password",
        role=RoleEnum.ANALYST,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_category(db: Session):
    """Create a test category"""
    category = Category(
        category_name="Test Category",
        description="Test category for testing"
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_root_endpoint(self, client):
        """Test GET /"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data

    def test_health_check_endpoint(self, client):
        """Test GET /health"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_websocket_health_endpoint(self, client):
        """Test GET /ws/health"""
        response = client.get("/ws/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestUsersAPI:
    """Test users API endpoints"""

    def test_list_users_empty(self, client):
        """Test GET /users with no users"""
        response = client.get("/users")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["total"] == 0
        assert data["count"] == 0
        assert len(data["users"]) == 0

    def test_create_user(self, client, db: Session):
        """Test POST /users creates user"""
        response = client.post("/users", json={
            "username": "newuser",
            "password": "password123",
            "role": "ANALYST",
            "assigned_categories": ["purchases"]
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["username"] == "newuser"
        assert data["role"] == "ANALYST"

        # Verify user was created in database
        user = db.query(User).filter(User.username == "newuser").first()
        assert user is not None
        assert user.role == RoleEnum.ANALYST

    def test_create_user_duplicate_username(self, client, test_user):
        """Test POST /users with duplicate username fails"""
        response = client.post("/users", json={
            "username": "testuser",
            "password": "password123",
            "role": "ANALYST"
        })

        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"]

    def test_create_user_invalid_role(self, client):
        """Test POST /users with invalid role fails"""
        response = client.post("/users", json={
            "username": "newuser",
            "password": "password123",
            "role": "INVALID_ROLE"
        })

        assert response.status_code == 400

    def test_list_users(self, client, test_user):
        """Test GET /users returns users"""
        response = client.get("/users")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["count"] == 1
        assert len(data["users"]) == 1
        assert data["users"][0]["username"] == "testuser"

    def test_list_users_with_filter(self, client, db: Session):
        """Test GET /users with role filter"""
        # Create two users with different roles
        admin = User(
            username="admin",
            password_hash="hash",
            role=RoleEnum.ADMIN,
            is_active=True
        )
        analyst = User(
            username="analyst",
            password_hash="hash",
            role=RoleEnum.ANALYST,
            is_active=True
        )
        db.add_all([admin, analyst])
        db.commit()

        # Filter by ADMIN
        response = client.get("/users?role=ADMIN")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["users"][0]["role"] == "ADMIN"

    def test_get_user_detail(self, client, test_user):
        """Test GET /users/{user_id}"""
        response = client.get(f"/users/{test_user.user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == test_user.user_id
        assert data["username"] == "testuser"
        assert data["role"] == "ANALYST"

    def test_get_user_not_found(self, client):
        """Test GET /users/{user_id} not found"""
        response = client.get("/users/nonexistent_id")
        assert response.status_code == 404

    def test_update_user(self, client, test_user, db: Session):
        """Test PUT /users/{user_id} updates user"""
        response = client.put(
            f"/users/{test_user.user_id}",
            json={
                "username": "updateduser",
                "role": "MANAGER"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updateduser"
        assert data["role"] == "MANAGER"

        # Verify in database
        user = db.query(User).filter(User.user_id == test_user.user_id).first()
        assert user.username == "updateduser"
        assert user.role == RoleEnum.MANAGER

    def test_update_user_status(self, client, test_user, db: Session):
        """Test PUT /users/{user_id}/status changes status"""
        response = client.put(
            f"/users/{test_user.user_id}/status",
            json={"is_active": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

        # Verify in database
        user = db.query(User).filter(User.user_id == test_user.user_id).first()
        assert user.is_active is False

class TestCategoriesAPI:
    """Test categories API endpoints"""

    def test_list_categories_empty(self, client):
        """Test GET /categories with no categories"""
        response = client.get("/categories")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["count"] == 0

    def test_create_category(self, client, db: Session):
        """Test POST /categories creates category"""
        response = client.post("/categories", json={
            "category_name": "Utilities",
            "description": "Utility payments"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["category_name"] == "Utilities"

        # Verify in database
        category = db.query(Category).filter(
            Category.category_name == "Utilities"
        ).first()
        assert category is not None

    def test_create_category_duplicate(self, client, test_category):
        """Test POST /categories with duplicate name fails"""
        response = client.post("/categories", json={
            "category_name": "Test Category",
            "description": "Duplicate"
        })

        assert response.status_code == 400

    def test_list_categories(self, client, test_category):
        """Test GET /categories returns categories"""
        response = client.get("/categories")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["count"] == 1

    def test_get_category_detail(self, client, test_category):
        """Test GET /categories/{category_id}"""
        response = client.get(f"/categories/{test_category.category_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["category_id"] == test_category.category_id
        assert data["category_name"] == "Test Category"

    def test_get_category_not_found(self, client):
        """Test GET /categories/{category_id} not found"""
        response = client.get("/categories/nonexistent_id")
        assert response.status_code == 404

    def test_update_category(self, client, test_category, db: Session):
        """Test PUT /categories/{category_id}"""
        response = client.put(
            f"/categories/{test_category.category_id}",
            json={
                "category_name": "Updated Category",
                "description": "Updated description"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["category_name"] == "Updated Category"

        # Verify in database
        category = db.query(Category).filter(
            Category.category_id == test_category.category_id
        ).first()
        assert category.category_name == "Updated Category"


class TestAuditLogsAPI:
    """Test audit logs API endpoints"""

    def test_list_audit_logs_empty(self, client):
        """Test GET /audit-logs with no logs"""
        response = client.get("/audit-logs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["count"] == 0

    def test_list_audit_logs_pagination(self, client):
        """Test GET /audit-logs pagination parameters"""
        # Test skip parameter
        response = client.get("/audit-logs?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 10

    def test_list_audit_logs_max_limit(self, client):
        """Test GET /audit-logs respects max limit"""
        response = client.get("/audit-logs?limit=1000")
        assert response.status_code == 200
        data = response.json()
        # Limit should be capped at 500
        assert data["limit"] <= 500


class TestAnomaliesAPI:
    """Test anomalies API endpoints"""

    def test_list_anomalies_empty(self, client):
        """Test GET /anomalies with no anomalies"""
        response = client.get("/anomalies")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["count"] == 0
        assert len(data["anomalies"]) == 0

    def test_anomalies_pagination(self, client):
        """Test GET /anomalies pagination"""
        response = client.get("/anomalies?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "skip" in data
        assert "limit" in data


class TestResponseFormat:
    """Test response format consistency"""

    def test_success_response_format(self, client):
        """Test successful response has correct format"""
        response = client.get("/users")
        assert response.status_code == 200
        data = response.json()

        # All responses should have status field
        assert "status" in data
        assert data["status"] == "success"

    def test_error_response_format(self, client):
        """Test error response has correct format"""
        response = client.get("/users/nonexistent")
        assert response.status_code == 404
        data = response.json()

        # Error responses should have detail
        assert "detail" in data

    def test_list_response_format(self, client):
        """Test list response has pagination fields"""
        response = client.get("/users")
        data = response.json()

        # List responses should have these fields
        assert "status" in data
        assert "total" in data
        assert "count" in data
        assert "skip" in data
        assert "limit" in data


class TestInputValidation:
    """Test input validation"""

    def test_invalid_json_rejected(self, client):
        """Test invalid JSON is rejected"""
        response = client.post(
            "/users",
            content="not json",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """Test missing required fields rejected"""
        response = client.post("/users", json={
            "username": "user"
            # Missing password and role
        })
        assert response.status_code == 422

    def test_invalid_enum_value(self, client):
        """Test invalid enum value rejected"""
        response = client.post("/users", json={
            "username": "user",
            "password": "pass",
            "role": "INVALID"
        })
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
