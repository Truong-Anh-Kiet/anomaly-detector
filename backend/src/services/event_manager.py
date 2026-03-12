"""
WebSocket Event System
Real-time event broadcasting for anomaly detection system
"""

from typing import Callable, Dict, List, Set
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """WebSocket event types"""
    ANOMALY_DETECTED = "anomaly_detected"
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    USER_ACTION = "user_action"
    SYSTEM_ALERT = "system_alert"
    AUDIT_LOG = "audit_log"
    THRESHOLD_UPDATED = "threshold_updated"
    CONNECTION_ESTABLISHED = "connection_established"
    HEARTBEAT = "heartbeat"


class Severity(str, Enum):
    """Notification severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class AnomalyEvent:
    """Anomaly detection event"""
    event_type: EventType = EventType.ANOMALY_DETECTED
    anomaly_id: str = ""
    category: str = ""
    score: float = 0.0
    threshold: float = 0.0
    severity: Severity = Severity.WARNING
    message: str = ""
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        return data


@dataclass
class ThresholdEvent:
    """Threshold alert event"""
    event_type: EventType = EventType.THRESHOLD_EXCEEDED
    category: str = ""
    current_value: float = 0.0
    threshold: float = 0.0
    severity: Severity = Severity.ERROR
    message: str = ""
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        return data


@dataclass
class UserActionEvent:
    """User action event for audit trail"""
    event_type: EventType = EventType.USER_ACTION
    user_id: str = ""
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    details: dict = None
    severity: Severity = Severity.INFO
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.details is None:
            self.details = {}

    def to_dict(self) -> dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        return data


@dataclass
class SystemAlertEvent:
    """System-level alert event"""
    event_type: EventType = EventType.SYSTEM_ALERT
    alert_type: str = ""
    severity: Severity = Severity.WARNING
    title: str = ""
    message: str = ""
    details: dict = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.details is None:
            self.details = {}

    def to_dict(self) -> dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        return data


class EventConnection:
    """Represents a WebSocket connection"""

    def __init__(self, connection_id: str, user_id: str, role: str):
        self.connection_id = connection_id
        self.user_id = user_id
        self.role = role
        self.subscribed_events: Set[EventType] = set()
        self.connected_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()

    def can_receive(self, event_type: EventType) -> bool:
        """Check if connection can receive event type"""
        if event_type in self.subscribed_events:
            return True
        # All users subscribe to heartbeat by default
        if event_type == EventType.HEARTBEAT:
            return True
        return False

    def subscribe(self, event_type: EventType):
        """Subscribe to event type"""
        self.subscribed_events.add(event_type)

    def unsubscribe(self, event_type: EventType):
        """Unsubscribe from event type"""
        self.subscribed_events.discard(event_type)

    def update_heartbeat(self):
        """Update last heartbeat timestamp"""
        self.last_heartbeat = datetime.utcnow()


class EventManager:
    """Manages WebSocket connections and event broadcasting"""

    def __init__(self):
        self.connections: Dict[str, EventConnection] = {}
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.event_history: List[dict] = []
        self.max_history_size = 1000

    def add_connection(self, connection: EventConnection):
        """Register a new WebSocket connection"""
        self.connections[connection.connection_id] = connection
        logger.info(f"Connection added: {connection.connection_id} (User: {connection.user_id})")

    def remove_connection(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.connections:
            conn = self.connections.pop(connection_id)
            logger.info(f"Connection removed: {connection_id} (User: {conn.user_id})")

    def get_connection(self, connection_id: str) -> EventConnection:
        """Get connection by ID"""
        return self.connections.get(connection_id)

    def get_user_connections(self, user_id: str) -> List[EventConnection]:
        """Get all connections for a user"""
        return [
            conn for conn in self.connections.values()
            if conn.user_id == user_id
        ]

    def subscribe_to_event(self, connection_id: str, event_type: EventType):
        """Subscribe a connection to an event type"""
        conn = self.get_connection(connection_id)
        if conn:
            conn.subscribe(event_type)
            logger.debug(f"Connection {connection_id} subscribed to {event_type.value}")

    def unsubscribe_from_event(self, connection_id: str, event_type: EventType):
        """Unsubscribe a connection from an event type"""
        conn = self.get_connection(connection_id)
        if conn:
            conn.unsubscribe(event_type)
            logger.debug(f"Connection {connection_id} unsubscribed from {event_type.value}")

    def register_handler(self, event_type: EventType, handler: Callable):
        """Register a callback handler for an event type"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    async def broadcast_event(self, event: dict, event_type: EventType = None):
        """Broadcast event to all subscribed connections"""
        if event_type:
            event['event_type'] = event_type.value
            event['type'] = event_type.value
        
        # Add to history
        self._add_to_history(event)

        # Call registered handlers
        if event_type and event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if hasattr(handler, '__call__'):
                        result = handler(event)
                        # Handle async handlers
                        import inspect
                        if inspect.iscoroutine(result):
                            await result
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")

        # Save event to database (can be overridden in subclass)
        await self._persist_event(event)

        return event

    async def broadcast_to_role(self, event: dict, role: str, event_type: EventType = None):
        """Broadcast event only to connections with specific role"""
        if event_type:
            event['event_type'] = event_type.value

        recipients = [
            conn for conn in self.connections.values()
            if conn.role == role and conn.can_receive(event_type)
        ]

        logger.info(f"Broadcasting to {len(recipients)} {role} connections")
        return recipients, event

    async def broadcast_to_user(self, user_id: str, event: dict, event_type: EventType = None):
        """Broadcast event to specific user's connections"""
        if event_type:
            event['event_type'] = event_type.value

        recipients = self.get_user_connections(user_id)
        logger.info(f"Broadcasting to user {user_id}: {len(recipients)} connections")
        return recipients, event

    def _add_to_history(self, event: dict):
        """Add event to in-memory history"""
        event_with_timestamp = {
            **event,
            'stored_at': datetime.utcnow().isoformat()
        }
        self.event_history.append(event_with_timestamp)
        
        # Keep history size bounded
        if len(self.event_history) > self.max_history_size:
            self.event_history.pop(0)

    async def _persist_event(self, event: dict):
        """Persist event to database (can be overridden)"""
        # This will be implemented in the API layer
        pass

    def get_connection_stats(self) -> dict:
        """Get connection statistics"""
        total_connections = len(self.connections)
        role_breakdown = {}
        
        for conn in self.connections.values():
            role = conn.role
            role_breakdown[role] = role_breakdown.get(role, 0) + 1

        return {
            "total_connections": total_connections,
            "by_role": role_breakdown,
            "history_size": len(self.event_history),
        }


# Global event manager instance
event_manager = EventManager()


def get_event_manager() -> EventManager:
    """Get the global event manager"""
    return event_manager
