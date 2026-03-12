"""
Anomaly Event Broadcasting Service
Broadcasts anomaly detection and threshold events in real-time
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from src.models import Anomaly
from src.services.event_manager import (
    AnomalyEvent,
    EventType,
    Severity,
    SystemAlertEvent,
    ThresholdEvent,
    UserActionEvent,
    get_event_manager,
)

logger = logging.getLogger(__name__)


class AnomalyEventBroadcaster:
    """Handles broadcasting of anomaly-related events"""

    def __init__(self):
        self.event_manager = get_event_manager()

    async def broadcast_anomaly_detected(
        self,
        anomaly: Anomaly,
        db: Session | None = None,
    ):
        """
        Broadcast anomaly detection event

        Args:
            anomaly: Detected anomaly object
            db: Database session (optional)
        """
        try:
            # Determine severity based on score
            if anomaly.score >= 0.9:
                severity = Severity.ERROR
            elif anomaly.score >= 0.75:
                severity = Severity.WARNING
            else:
                severity = Severity.INFO

            event = AnomalyEvent(
                anomaly_id=anomaly.anomaly_id,
                category=anomaly.category,
                score=anomaly.score,
                threshold=anomaly.threshold,
                severity=severity,
                message=f"Anomaly detected in {anomaly.category}: score {anomaly.score:.2f}"
            )

            # Broadcast event
            await self.event_manager.broadcast_event(
                event.to_dict(),
                EventType.ANOMALY_DETECTED
            )

            logger.info(
                f"Anomaly event broadcasted: {anomaly.anomaly_id} "
                f"(category={anomaly.category}, score={anomaly.score})"
            )

        except Exception as e:
            logger.error(f"Error broadcasting anomaly event: {e}")

    async def broadcast_threshold_exceeded(
        self,
        category: str,
        current_value: float,
        threshold: float,
        db: Session | None = None,
    ):
        """
        Broadcast threshold exceeded event

        Args:
            category: Anomaly category
            current_value: Current metric value
            threshold: Threshold value
            db: Database session (optional)
        """
        try:
            percentage = (current_value / threshold * 100) if threshold > 0 else 0

            event = ThresholdEvent(
                category=category,
                current_value=current_value,
                threshold=threshold,
                severity=Severity.ERROR,
                message=(
                    f"Threshold exceeded for {category}: "
                    f"{current_value:.2f} > {threshold:.2f} ({percentage:.1f}%)"
                )
            )

            await self.event_manager.broadcast_event(
                event.to_dict(),
                EventType.THRESHOLD_EXCEEDED
            )

            logger.warning(
                f"Threshold exceeded: {category} ({percentage:.1f}%)"
            )

        except Exception as e:
            logger.error(f"Error broadcasting threshold event: {e}")

    async def broadcast_user_action(
        self,
        user_id: str,
        action: str,
        resource_type: str = "",
        resource_id: str = "",
        details: dict = None,
        db: Session | None = None,
    ):
        """
        Broadcast user action event

        Args:
            user_id: User performing action
            action: Action name (e.g., "update_status", "export_data")
            resource_type: Type of resource (e.g., "anomaly", "threshold")
            resource_id: ID of resource being acted upon
            details: Additional action details
            db: Database session (optional)
        """
        try:
            event = UserActionEvent(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                severity=Severity.INFO
            )

            await self.event_manager.broadcast_event(
                event.to_dict(),
                EventType.USER_ACTION
            )

            logger.info(
                f"User action broadcasted: {user_id} - {action} "
                f"({resource_type}:{resource_id})"
            )

        except Exception as e:
            logger.error(f"Error broadcasting user action: {e}")

    async def broadcast_system_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        severity: Severity = Severity.WARNING,
        details: dict = None,
    ):
        """
        Broadcast system-level alert

        Args:
            alert_type: Type of system alert
            title: Alert title
            message: Alert message
            severity: Alert severity level
            details: Additional alert details
        """
        try:
            event = SystemAlertEvent(
                alert_type=alert_type,
                title=title,
                message=message,
                severity=severity,
                details=details or {}
            )

            await self.event_manager.broadcast_event(
                event.to_dict(),
                EventType.SYSTEM_ALERT
            )

            logger.warning(f"System alert broadcasted: {title}")

        except Exception as e:
            logger.error(f"Error broadcasting system alert: {e}")

    async def broadcast_to_role(
        self,
        role: str,
        event_dict: dict,
        event_type: EventType,
    ):
        """Broadcast event to specific role only"""
        try:
            recipients, event = await self.event_manager.broadcast_to_role(
                event_dict,
                role,
                event_type
            )
            logger.info(f"Event broadcasted to {len(recipients)} {role} users")
        except Exception as e:
            logger.error(f"Error broadcasting to role: {e}")

    async def broadcast_to_user(
        self,
        user_id: str,
        event_dict: dict,
        event_type: EventType,
    ):
        """Broadcast event to specific user only"""
        try:
            recipients, event = await self.event_manager.broadcast_to_user(
                user_id,
                event_dict,
                event_type
            )
            logger.info(f"Event broadcasted to user {user_id} ({len(recipients)} connections)")
        except Exception as e:
            logger.error(f"Error broadcasting to user: {e}")


# Global broadcaster instance
_broadcaster: AnomalyEventBroadcaster | None = None


def get_anomaly_broadcaster() -> AnomalyEventBroadcaster:
    """Get or create anomaly event broadcaster"""
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = AnomalyEventBroadcaster()
    return _broadcaster
