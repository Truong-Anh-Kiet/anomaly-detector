"""Audit log API endpoints with WebSocket integration"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import logging
from datetime import datetime

from src.database import get_db
from src.models.audit_log import AuditLog
from src.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("", response_model=dict)
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    user_id: str = Query(None),
    action: str = Query(None),
    resource_type: str = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    """
    List audit logs with optional filtering.
    
    Query Parameters:
    - skip: Number of results to skip (pagination)
    - limit: Number of results to return (max 500)
    - user_id: Filter by user who performed action
    - action: Filter by action type
    - resource_type: Filter by resource type (anomaly, user, category, etc.)
    
    Returns:
        - total: Total logs matching filters
        - count: Number of logs in this page
        - logs: List of audit logs
    """
    try:
        query = db.query(AuditLog)
        
        # Apply filters
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        logs = query.order_by(
            AuditLog.timestamp.desc()
        ).offset(skip).limit(limit).all()
        
        # Convert to response format
        log_items = []
        for log in logs:
            # Get user info
            user = db.query(User).filter(User.user_id == log.user_id).first()
            
            log_items.append({
                "log_id": log.log_id,
                "user_id": log.user_id,
                "username": user.username if user else "Unknown",
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details if hasattr(log, 'details') else None,
                "timestamp": log.timestamp.isoformat(),
                "ip_address": log.ip_address if hasattr(log, 'ip_address') else None,
            })
        
        return {
            "status": "success",
            "total": total,
            "count": len(log_items),
            "skip": skip,
            "limit": limit,
            "logs": log_items
        }
        
    except Exception as e:
        logger.error(f"Error listing audit logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list audit logs: {str(e)}")


@router.get("/{log_id}", response_model=dict)
async def get_audit_log_detail(
    log_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get detailed information about a specific audit log entry.
    
    Returns:
        - log_id: Audit log ID
        - user_id: User who performed the action
        - username: Username of the user
        - action: Action performed
        - resource_type: Type of resource affected
        - resource_id: ID of the resource
        - details: Additional details about the action
        - timestamp: When the action occurred
        - ip_address: IP address of the requester
    """
    try:
        log = db.query(AuditLog).filter(AuditLog.log_id == log_id).first()
        
        if not log:
            raise HTTPException(status_code=404, detail="Audit log not found")
        
        user = db.query(User).filter(User.user_id == log.user_id).first()
        
        return {
            "status": "success",
            "log_id": log.log_id,
            "user_id": log.user_id,
            "username": user.username if user else "Unknown",
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details if hasattr(log, 'details') else None,
            "timestamp": log.timestamp.isoformat(),
            "ip_address": log.ip_address if hasattr(log, 'ip_address') else None,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit log detail: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get audit log: {str(e)}")


@router.get("/user/{user_id}/actions")
async def get_user_audit_trail(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get audit trail for a specific user's actions.
    
    Query Parameters:
    - skip: Number of results to skip
    - limit: Number of results to return
    - days: Look back N days (default 30)
    
    Returns:
        - user_id: User ID
        - total_actions: Total actions by user
        - logs: List of audit logs
    """
    try:
        # Verify user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get logs from the specified period
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(AuditLog).filter(
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= start_date
        )
        
        total = query.count()
        
        logs = query.order_by(
            AuditLog.timestamp.desc()
        ).offset(skip).limit(limit).all()
        
        log_items = [
            {
                "log_id": log.log_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "timestamp": log.timestamp.isoformat(),
                "details": log.details if hasattr(log, 'details') else None,
            }
            for log in logs
        ]
        
        return {
            "status": "success",
            "user_id": user_id,
            "username": user.username,
            "total_actions": total,
            "count": len(log_items),
            "skip": skip,
            "limit": limit,
            "logs": log_items
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user audit trail: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get audit trail: {str(e)}")
