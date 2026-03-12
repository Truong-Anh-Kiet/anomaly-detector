"""RBAC middleware for FastAPI routes"""

import logging
from functools import wraps

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

# Role-based permission matrix
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "view_anomalies",
        "export_anomalies",
        "manage_models",
        "manage_users",
        "configure_thresholds",
        "view_audit_logs",
        "update_settings",
    },
    "analyst": {
        "view_anomalies",
        "export_anomalies",
        "configure_thresholds",
        "view_audit_logs",
    },
    "auditor": {
        "view_audit_logs",
        "view_anomalies",  # Read-only
    },
    "guest": {
        "view_anomalies",  # Limited access
    },
}


class RBACMiddleware:
    """Role-based access control enforcement"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        """
        ASGI middleware to attach user context to request.
        User comes from JWT token (validated by auth middleware).
        """
        if scope["type"] == "http":
            request = Request(scope)
            user = getattr(request.state, "user", None)
            if user:
                scope["user"] = user
        await self.app(scope, receive, send)


def require_permission(required_permission: str):
    """
    Decorator for route-level RBAC enforcement.

    Usage:
        @router.post("/anomalies/export")
        @require_permission("export_anomalies")
        async def export_anomalies(request: Request):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request = None, **kwargs):
            # Extract user from request state (set by auth middleware)
            user = getattr(request.state, "user", None)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unauthenticated",
                )

            # Get user role
            user_role = user.role if hasattr(user, "role") else "guest"

            # Check if role has permission
            if user_role not in ROLE_PERMISSIONS:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Unknown role: {user_role}",
                )

            if required_permission not in ROLE_PERMISSIONS[user_role]:
                logger.warning(
                    f"User {user.user_id} with role {user_role} "
                    f"attempted unauthorized action: {required_permission}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {required_permission}",
                )

            # Call the actual route handler
            return await func(*args, request=request, **kwargs)

        return wrapper

    return decorator


def require_role(required_roles: list[str]):
    """
    Decorator for role-level RBAC enforcement.

    Usage:
        @router.post("/models/upload")
        @require_role(["admin", "analyst"])
        async def upload_model(request: Request):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request = None, **kwargs):
            user = getattr(request.state, "user", None)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unauthenticated",
                )

            user_role = user.role if hasattr(user, "role") else "guest"

            if user_role not in required_roles:
                logger.warning(
                    f"User {user.user_id} with role {user_role} denied access "
                    f"(required roles: {required_roles})"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"This action requires one of: {', '.join(required_roles)}",
                )

            return await func(*args, request=request, **kwargs)

        return wrapper

    return decorator


def get_user_permissions(user_role: str) -> set[str]:
    """Get all permissions for a given role"""
    return ROLE_PERMISSIONS.get(user_role, set())


def check_permission(user_role: str, required_permission: str) -> bool:
    """Check if a role has a specific permission"""
    return required_permission in get_user_permissions(user_role)
