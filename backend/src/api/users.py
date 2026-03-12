"""User management API endpoints with WebSocket broadcast integration"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.user import RoleEnum, User
from src.services.anomaly_broadcaster import get_anomaly_broadcaster
from src.services.auth_service import get_password_hash

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


class UserCreateRequest(BaseModel):
    """Request schema for creating a user"""
    username: str
    password: str
    role: str  # ADMIN, MANAGER, ANALYST
    assigned_categories: list[str] = None


class UserUpdateRequest(BaseModel):
    """Request schema for updating a user"""
    username: str = None
    role: str = None
    assigned_categories: list[str] = None
    is_active: bool = None


@router.get("", response_model=dict)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    role: str = Query(None),
    is_active: bool = Query(None),
    db: Session = Depends(get_db), # noqa: B008
) -> dict:
    """
    List all users with optional filtering.

    Query Parameters:
    - skip: Number of results to skip (pagination)
    - limit: Number of results to return (max 500)
    - role: Filter by role (ADMIN, MANAGER, ANALYST)
    - is_active: Filter by active status

    Returns:
        - total: Total users matching filters
        - count: Number of users in this page
        - users: List of user objects
    """
    try:
        query = db.query(User)

        # Apply filters
        if role:
            try:
                query = query.filter(User.role == RoleEnum[role.upper()])
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid role: {role}") from None

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        # Get total count
        total = query.count()

        # Get paginated results
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

        # Convert to response format
        user_items = [
            {
                "user_id": u.user_id,
                "username": u.username,
                "role": u.role.value,
                "assigned_categories": u.assigned_categories or [],
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
                "last_login": u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ]

        return {
            "status": "success",
            "total": total,
            "count": len(user_items),
            "skip": skip,
            "limit": limit,
            "users": user_items
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}") from e


@router.get("/{user_id}", response_model=dict)
async def get_user_detail(
    user_id: str,
    db: Session = Depends(get_db), # noqa: B008
) -> dict:
    """
    Get detailed information about a specific user.

    Returns:
        - user_id: User ID
        - username: Username
        - role: User role
        - assigned_categories: Assigned transaction categories
        - is_active: Whether user is active
        - created_at: Account creation date
        - last_login: Last login timestamp
    """
    try:
        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "status": "success",
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "assigned_categories": user.assigned_categories or [],
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user detail: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}") from e


@router.post("", response_model=dict)
async def create_user(
    user_data: UserCreateRequest,
    current_user_id: str = Depends(lambda: "system"),  # In real app, extract from JWT
    db: Session = Depends(get_db), # noqa: B008
) -> dict:
    """
    Create a new user.

    This endpoint:
    1. Validates user data
    2. Creates user in database
    3. Broadcasts user_created event

    Returns:
        - user_id: New user ID
        - username: Username
        - role: User role
        - message: Success message
    """
    try:
        # Check if username already exists
        existing_user = db.query(User).filter(
            User.username == user_data.username
        ).first()

        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        # Validate role
        try:
            role = RoleEnum[user_data.role.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Must be one of: {', '.join([r.value for r in RoleEnum])}"
            ) from None

        # Create new user
        new_user = User(
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            role=role,
            assigned_categories=user_data.assigned_categories or [],
            is_active=True
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Broadcast user creation event
        broadcaster = get_anomaly_broadcaster()
        await broadcaster.broadcast_user_action(
            user_id=current_user_id,
            action="user_created",
            resource_type="user",
            resource_id=new_user.user_id,
            details={
                "new_username": user_data.username,
                "role": role.value,
                "severity": "INFO"
            }
        )

        logger.info(f"User created: {new_user.username} (ID: {new_user.user_id})")

        return {
            "status": "success",
            "user_id": new_user.user_id,
            "username": new_user.username,
            "role": new_user.role.value,
            "assigned_categories": new_user.assigned_categories or [],
            "message": f"User '{user_data.username}' created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}") from e


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: str,
    user_data: UserUpdateRequest,
    current_user_id: str = Depends(lambda: "system"),  # In real app, extract from JWT
    db: Session = Depends(get_db), # noqa: B008
) -> dict:
    """
    Update user information.

    This endpoint:
    1. Finds user by ID
    2. Updates allowed fields
    3. Saves to database
    4. Broadcasts user_updated event

    Returns:
        - user_id: User ID
        - username: Updated username
        - role: Updated role
        - message: Success message
    """
    try:
        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        changes = {}

        # Update username if provided
        if user_data.username and user_data.username != user.username:
            # Check if new username already exists
            existing = db.query(User).filter(
                User.username == user_data.username,
                User.user_id != user_id
            ).first()

            if existing:
                raise HTTPException(status_code=400, detail="Username already exists")

            changes["username"] = user_data.username
            user.username = user_data.username

        # Update role if provided
        if user_data.role:
            try:
                new_role = RoleEnum[user_data.role.upper()]
                if new_role != user.role:
                    changes["role"] = new_role.value
                    user.role = new_role
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid role. Must be one of: {', '.join([r.value for r in RoleEnum])}"
                ) from None

        # Update assigned categories if provided
        if user_data.assigned_categories is not None:
            changes["assigned_categories"] = user_data.assigned_categories
            user.assigned_categories = user_data.assigned_categories

        # Update is_active if provided
        if user_data.is_active is not None:
            changes["is_active"] = user_data.is_active
            user.is_active = user_data.is_active

        db.commit()
        db.refresh(user)

        # Broadcast user update event if changes were made
        if changes:
            broadcaster = get_anomaly_broadcaster()
            await broadcaster.broadcast_user_action(
                user_id=current_user_id,
                action="user_updated",
                resource_type="user",
                resource_id=user_id,
                details={
                    "username": user.username,
                    "changes": changes,
                    "severity": "INFO"
                }
            )

        logger.info(f"User updated: {user.username} - Changes: {changes}")

        return {
            "status": "success",
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "assigned_categories": user.assigned_categories or [],
            "is_active": user.is_active,
            "message": f"User '{user.username}' updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}") from e


@router.put("/{user_id}/status", response_model=dict)
async def update_user_status(
    user_id: str,
    status_data: dict,  # {"is_active": true/false}
    current_user_id: str = Depends(lambda: "system"),
    db: Session = Depends(get_db), # noqa: B008
) -> dict:
    """
    Update user active/inactive status.

    This endpoint:
    1. Finds user by ID
    2. Updates active status
    3. Broadcasts status_changed event

    Returns:
        - user_id: User ID
        - is_active: New active status
        - message: Success message
    """
    try:
        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if "is_active" not in status_data:
            raise HTTPException(status_code=400, detail="is_active field required")

        new_status = status_data["is_active"]

        if user.is_active != new_status:
            user.is_active = new_status
            db.commit()
            db.refresh(user)

            # Broadcast status change event
            broadcaster = get_anomaly_broadcaster()
            await broadcaster.broadcast_user_action(
                user_id=current_user_id,
                action="status_changed",
                resource_type="user",
                resource_id=user_id,
                details={
                    "username": user.username,
                    "old_status": not new_status,
                    "new_status": new_status,
                    "severity": "WARNING" if not new_status else "INFO"
                }
            )

            logger.info(f"User status changed: {user.username} - Active: {new_status}")

        return {
            "status": "success",
            "user_id": user.user_id,
            "username": user.username,
            "is_active": user.is_active,
            "message": f"User status updated to {'active' if new_status else 'inactive'}"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update user status: {str(e)}") from e
