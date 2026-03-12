"""FastAPI dependencies for shared components across routes"""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.config import Settings, get_settings
from src.database import SessionLocal
from src.models import RoleEnum, User
from src.services.auth_service import AuthService

logger = logging.getLogger(__name__)

# Database dependency
def get_db() -> Session:
    """Get database session for route handlers"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Settings dependency
def get_app_settings() -> Settings:
    """Get application settings"""
    return get_settings()


# Auth service dependency
_auth_service = None


def get_auth_service() -> AuthService:
    """Get authentication service"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


# Security scheme
security = HTTPBearer()


# JWT verification dependency
async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security), # noqa: B008
    db: Session = Depends(get_db), # noqa: B008
    auth_service: AuthService = Depends(get_auth_service), # noqa: B008
) -> User:
    """
    Get current authenticated user from JWT token.
    Validates JWT signature and expiration.
    """
    token = credentials.credentials

    # Verify token
    token_payload = auth_service.verify_token(token)
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = db.query(User).filter(User.user_id == token_payload.sub).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# Role-based authorization dependencies
async def get_admin_user(
    current_user: User = Depends(get_current_user), # noqa: B008
) -> User:
    """Allow only Admin role"""
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_manager_or_admin_user(
    current_user: User = Depends(get_current_user), # noqa: B008
) -> User:
    """Allow Manager and Admin roles"""
    if current_user.role not in (RoleEnum.MANAGER, RoleEnum.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or Admin access required",
        )
    return current_user


async def authorize_category_access(
    category: str,
    current_user: User = Depends(get_current_user), # noqa: B008
) -> str:
    """
    Authorize user access to a specific category.
    Admin/Manager can access all categories.
    Analyst can only access assigned categories.
    """
    if current_user.role in (RoleEnum.ADMIN, RoleEnum.MANAGER):
        return category

    # Analyst role
    if current_user.role == RoleEnum.ANALYST:
        assigned = current_user.assigned_categories or []
        if category not in assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to category '{category}'",
            )
        return category

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions",
    )
