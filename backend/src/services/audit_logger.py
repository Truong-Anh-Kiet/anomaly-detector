"""Audit logging service for compliance and audit trails"""

import logging
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.models import AuditLog, User

logger = logging.getLogger(__name__)


class AuditLoggerService:
    """Service for recording and querying audit logs"""

    # 1-year retention policy
    ARCHIVE_DAYS = 365
    DELETE_DAYS = 730

    def log_action(
        self,
        db: Session,
        user_id: str,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        details: dict = None,
    ) -> AuditLog:
        """
        Log a user action to audit trail.
        
        Args:
            db: Database session
            user_id: ID of user performing action
            action: Action name (e.g., "login", "view_anomalies", "upload_model")
            resource_type: Type of resource affected (e.g., "anomaly", "model", "user")
            resource_id: ID of resource affected
            details: Additional context as dict
            
        Returns:
            Created AuditLog object
        """
        try:
            log_entry = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=json.dumps(details) if details else None,
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            
            logger.debug(
                f"Logged action: {action} by user {user_id} on {resource_type}:{resource_id}"
            )
            return log_entry
        except Exception as e:
            logger.error(f"Failed to log action: {e}")
            db.rollback()
            raise

    def log_anomaly_detection(
        self,
        db: Session,
        detection_id: str,
        category: str,
        amount: float,
        model_version: str,
    ) -> AuditLog:
        """Log an anomaly detection event"""
        return self.log_action(
            db,
            user_id=None,  # System-generated, no user
            action="anomaly_detected",
            resource_type="anomaly",
            resource_id=detection_id,
            details={
                "category": category,
                "amount": amount,
                "model_version": model_version,
            },
        )

    def get_audit_logs(
        self,
        db: Session,
        user_id: str = None,
        action: str = None,
        days: int = 30,
        exclude_archived: bool = True,
    ) -> list:
        """
        Query audit logs with filters.
        
        Args:
            db: Database session
            user_id: Filter by user ID
            action: Filter by action name
            days: Look back days (default 30)
            exclude_archived: Exclude soft-deleted logs
            
        Returns:
            List of AuditLog objects
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = db.query(AuditLog).filter(AuditLog.timestamp >= cutoff_date)

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        if action:
            query = query.filter(AuditLog.action == action)

        if exclude_archived:
            query = query.filter(AuditLog.archived_at == None)

        return query.order_by(AuditLog.timestamp.desc()).all()

    def archive_old_logs(self, db: Session) -> int:
        """
        Archive logs older than ARCHIVE_DAYS (soft-delete).
        
        Returns:
            Number of logs archived
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.ARCHIVE_DAYS)

        archived_count = (
            db.query(AuditLog)
            .filter(
                AuditLog.timestamp < cutoff_date,
                AuditLog.archived_at == None,
            )
            .update({"archived_at": datetime.utcnow()})
        )
        db.commit()

        logger.info(f"Archived {archived_count} audit logs")
        return archived_count

    def hard_delete_old_logs(self, db: Session) -> int:
        """
        Permanently delete logs older than DELETE_DAYS.
        
        Returns:
            Number of logs deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.DELETE_DAYS)

        deleted_count = (
            db.query(AuditLog)
            .filter(AuditLog.timestamp < cutoff_date)
            .delete()
        )
        db.commit()

        logger.info(f"Hard-deleted {deleted_count} old audit logs")
        return deleted_count

    def cleanup_audit_logs(self, db: Session):
        """Run full cleanup cycle (archive + hard delete)"""
        archived = self.archive_old_logs(db)
        deleted = self.hard_delete_old_logs(db)
        logger.info(f"Audit log cleanup: archived={archived}, deleted={deleted}")
