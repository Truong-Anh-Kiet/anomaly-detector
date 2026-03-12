"""Unit tests for event management services - Phase 9"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from src.services.anomaly_broadcaster import AnomalyEventBroadcaster
from src.services.event_manager import (
    AnomalyEvent,
    EventConnection,
    EventManager,
    EventType,
    Severity,
    SystemAlertEvent,
    ThresholdEvent,
    UserActionEvent,
)
from src.services.websocket_handler import WebSocketHandler


class TestEventType:
    """Test EventType enum"""
    
    def test_event_type_values(self):
        """Test all event types are defined"""
        assert EventType.ANOMALY_DETECTED.value == "anomaly_detected"
        assert EventType.THRESHOLD_EXCEEDED.value == "threshold_exceeded"
        assert EventType.USER_ACTION.value == "user_action"
        assert EventType.SYSTEM_ALERT.value == "system_alert"
        assert EventType.AUDIT_LOG.value == "audit_log"
        assert EventType.THRESHOLD_UPDATED.value == "threshold_updated"
        assert EventType.CONNECTION_ESTABLISHED.value == "connection_established"
        assert EventType.HEARTBEAT.value == "heartbeat"
    
    def test_severity_values(self):
        """Test all severity levels are defined"""
        assert Severity.INFO.value == "info"
        assert Severity.WARNING.value == "warning"
        assert Severity.ERROR.value == "error"
        assert Severity.SUCCESS.value == "success"


class TestEventDataclasses:
    """Test event dataclasses"""
    
    def test_anomaly_event_creation(self):
        """Test creating AnomalyEvent"""
        event = AnomalyEvent(
            anomaly_id="anom123",
            category="purchases",
            score=0.92,
            threshold=0.7,
            severity="high",
            message="High anomaly score detected",
            timestamp=datetime.utcnow()
        )
        
        assert event.anomaly_id == "anom123"
        assert event.score == 0.92
        assert event.category == "purchases"
    
    def test_anomaly_event_to_dict(self):
        """Test AnomalyEvent.to_dict() serialization"""
        now = datetime.utcnow()
        event = AnomalyEvent(
            anomaly_id="anom123",
            category="purchases",
            score=0.92,
            threshold=0.7,
            severity="high",
            message="Test message",
            timestamp=now
        )
        
        event_dict = event.to_dict()
        assert event_dict["anomaly_id"] == "anom123"
        assert event_dict["score"] == 0.92
        assert "timestamp" in event_dict
    
    def test_threshold_event_creation(self):
        """Test creating ThresholdEvent"""
        event = ThresholdEvent(
            category="spending",
            current_value=1500.0,
            threshold=1000.0,
            severity="high",
            message="Threshold exceeded",
            timestamp=datetime.utcnow()
        )
        
        assert event.category == "spending"
        assert event.current_value == 1500.0
        assert event.threshold == 1000.0
    
    def test_user_action_event_creation(self):
        """Test creating UserActionEvent"""
        event = UserActionEvent(
            user_id="user123",
            action="user_created",
            resource_type="user",
            resource_id="newuser456",
            details={"role": "ANALYST"},
            severity="info",
            timestamp=datetime.utcnow()
        )
        
        assert event.user_id == "user123"
        assert event.action == "user_created"
        assert event.resource_type == "user"
    
    def test_system_alert_event_creation(self):
        """Test creating SystemAlertEvent"""
        event = SystemAlertEvent(
            alert_type="db_connection_lost",
            severity="error",
            title="Database Connection Lost",
            message="Cannot connect to database",
            details={"error": "timeout"},
            timestamp=datetime.utcnow()
        )
        
        assert event.alert_type == "db_connection_lost"
        assert event.severity == "error"
        assert event.title == "Database Connection Lost"


class TestEventConnection:
    """Test EventConnection class"""
    
    def test_event_connection_creation(self):
        """Test creating EventConnection"""
        conn = EventConnection(
            connection_id="conn123",
            user_id="user456",
            role="ADMIN",
            subscribed_events={EventType.ANOMALY_DETECTED},
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )
        
        assert conn.connection_id == "conn123"
        assert conn.user_id == "user456"
        assert conn.role == "ADMIN"
        assert EventType.ANOMALY_DETECTED in conn.subscribed_events
    
    def test_can_receive_subscribed_event(self):
        """Test can_receive() for subscribed event"""
        conn = EventConnection(
            connection_id="conn123",
            user_id="user456",
            role="ANALYST",
            subscribed_events={EventType.ANOMALY_DETECTED},
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )
        
        assert conn.can_receive(EventType.ANOMALY_DETECTED) is True
        assert conn.can_receive(EventType.USER_ACTION) is False
    
    def test_subscribe_to_event(self):
        """Test subscribing to event type"""
        conn = EventConnection(
            connection_id="conn123",
            user_id="user456",
            role="ANALYST",
            subscribed_events=set(),
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )
        
        conn.subscribe(EventType.ANOMALY_DETECTED)
        assert EventType.ANOMALY_DETECTED in conn.subscribed_events
    
    def test_unsubscribe_from_event(self):
        """Test unsubscribing from event type"""
        conn = EventConnection(
            connection_id="conn123",
            user_id="user456",
            role="ANALYST",
            subscribed_events={EventType.ANOMALY_DETECTED},
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )
        
        conn.unsubscribe(EventType.ANOMALY_DETECTED)
        assert EventType.ANOMALY_DETECTED not in conn.subscribed_events
    
    def test_update_heartbeat(self):
        """Test updating heartbeat timestamp"""
        old_time = datetime.utcnow()
        conn = EventConnection(
            connection_id="conn123",
            user_id="user456",
            role="ANALYST",
            subscribed_events=set(),
            connected_at=old_time,
            last_heartbeat=old_time
        )
        
        new_time = datetime.utcnow()
        conn.update_heartbeat()
        assert conn.last_heartbeat > old_time


class TestEventManager:
    """Test EventManager class"""
    
    def test_event_manager_creation(self):
        """Test creating EventManager instance"""
        manager = EventManager()
        
        assert len(manager.connections) == 0
        assert len(manager.event_handlers) == 0
        assert len(manager.event_history) == 0
    
    def test_add_connection(self):
        """Test adding a connection"""
        manager = EventManager()
        conn = EventConnection(
            connection_id="conn123",
            user_id="user456",
            role="ANALYST",
            subscribed_events=set(),
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )
        
        manager.add_connection(conn)
        assert "conn123" in manager.connections
        assert manager.connections["conn123"].user_id == "user456"
    
    def test_remove_connection(self):
        """Test removing a connection"""
        manager = EventManager()
        conn = EventConnection(
            connection_id="conn123",
            user_id="user456",
            role="ANALYST",
            subscribed_events=set(),
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )
        
        manager.add_connection(conn)
        manager.remove_connection("conn123")
        assert "conn123" not in manager.connections
    
    def test_get_connection(self):
        """Test getting a connection"""
        manager = EventManager()
        conn = EventConnection(
            connection_id="conn123",
            user_id="user456",
            role="ANALYST",
            subscribed_events=set(),
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )
        
        manager.add_connection(conn)
        retrieved = manager.get_connection("conn123")
        assert retrieved is conn
        assert retrieved.user_id == "user456"
    
    def test_get_user_connections(self):
        """Test getting all connections for a user"""
        manager = EventManager()
        
        for i in range(3):
            conn = EventConnection(
                connection_id=f"conn{i}",
                user_id="user456",
                role="ANALYST",
                subscribed_events=set(),
                connected_at=datetime.utcnow(),
                last_heartbeat=datetime.utcnow()
            )
            manager.add_connection(conn)
        
        user_conns = manager.get_user_connections("user456")
        assert len(user_conns) == 3
    
    def test_subscribe_to_event(self):
        """Test subscribing connection to event"""
        manager = EventManager()
        conn = EventConnection(
            connection_id="conn123",
            user_id="user456",
            role="ANALYST",
            subscribed_events=set(),
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )
        manager.add_connection(conn)
        
        manager.subscribe_to_event("conn123", EventType.ANOMALY_DETECTED)
        assert EventType.ANOMALY_DETECTED in conn.subscribed_events
    
    def test_unsubscribe_from_event(self):
        """Test unsubscribing connection from event"""
        manager = EventManager()
        conn = EventConnection(
            connection_id="conn123",
            user_id="user456",
            role="ANALYST",
            subscribed_events={EventType.ANOMALY_DETECTED},
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )
        manager.add_connection(conn)
        
        manager.unsubscribe_from_event("conn123", EventType.ANOMALY_DETECTED)
        assert EventType.ANOMALY_DETECTED not in conn.subscribed_events
    
    def test_get_connection_stats(self):
        """Test getting connection statistics"""
        manager = EventManager()
        
        # Add ADMIN connection
        admin_conn = EventConnection(
            connection_id="admin1",
            user_id="admin",
            role="ADMIN",
            subscribed_events=set(),
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )
        manager.add_connection(admin_conn)
        
        # Add ANALYST connections
        for i in range(2):
            analyst_conn = EventConnection(
                connection_id=f"analyst{i}",
                user_id=f"analyst{i}",
                role="ANALYST",
                subscribed_events=set(),
                connected_at=datetime.utcnow(),
                last_heartbeat=datetime.utcnow()
            )
            manager.add_connection(analyst_conn)
        
        stats = manager.get_connection_stats()
        assert stats["total_connections"] == 3
        assert stats["by_role"]["ADMIN"] == 1
        assert stats["by_role"]["ANALYST"] == 2
    
    def test_broadcast_event(self):
        """Test broadcasting event to all subscribers"""
        manager = EventManager()
        
        # Add connections subscribed to anomaly events
        for i in range(2):
            conn = EventConnection(
                connection_id=f"conn{i}",
                user_id=f"user{i}",
                role="ANALYST",
                subscribed_events={EventType.ANOMALY_DETECTED},
                connected_at=datetime.utcnow(),
                last_heartbeat=datetime.utcnow()
            )
            manager.add_connection(conn)
        
        # Broadcast event
        event = AnomalyEvent(
            anomaly_id="anom123",
            category="purchases",
            score=0.92,
            threshold=0.7,
            severity="high",
            message="Test anomaly",
            timestamp=datetime.utcnow()
        )
        
        # Verify event is added to history
        manager.broadcast_event(EventType.ANOMALY_DETECTED, event)
        assert len(manager.event_history) == 1
        assert manager.event_history[0]["type"] == EventType.ANOMALY_DETECTED
    
    def test_event_history_max_size(self):
        """Test event history respects max size limit"""
        manager = EventManager()
        
        # Add many events
        for i in range(1100):
            event = AnomalyEvent(
                anomaly_id=f"anom{i}",
                category="purchases",
                score=0.92,
                threshold=0.7,
                severity="high",
                message=f"Event {i}",
                timestamp=datetime.utcnow()
            )
            manager.broadcast_event(EventType.ANOMALY_DETECTED, event)
        
        # History should be capped at 1000
        assert len(manager.event_history) <= 1000


class TestAnomalyEventBroadcaster:
    """Test AnomalyEventBroadcaster class"""
    
    @pytest.mark.asyncio
    async def test_broadcaster_creation(self):
        """Test creating broadcaster instance"""
        mock_manager = Mock()
        broadcaster = AnomalyEventBroadcaster(mock_manager)
        
        assert broadcaster.event_manager is mock_manager
    
    @pytest.mark.asyncio
    async def test_broadcast_anomaly_detected(self):
        """Test broadcasting anomaly detected event"""
        mock_manager = Mock()
        broadcaster = AnomalyEventBroadcaster(mock_manager)
        
        # Create test result with combined_score attribute
        mock_result = Mock()
        mock_result.detection_id = "det123"
        mock_result.combined_score = 0.92
        mock_result.stats_score = 0.85
        mock_result.ml_score = 0.95
        
        mock_db = Mock()
        
        # Call broadcast
        await broadcaster.broadcast_anomaly_detected(mock_result, mock_db)
        
        # Verify broadcast was called
        mock_manager.broadcast_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_severity_calculation(self):
        """Test severity is calculated based on score"""
        mock_manager = Mock()
        broadcaster = AnomalyEventBroadcaster(mock_manager)
        
        # Test ERROR severity (score >= 0.9)
        mock_result = Mock()
        mock_result.detection_id = "det1"
        mock_result.combined_score = 0.95
        mock_db = Mock()
        
        await broadcaster.broadcast_anomaly_detected(mock_result, mock_db)
        
        # Get the event that was broadcast
        call_args = mock_manager.broadcast_event.call_args
        assert call_args is not None


class TestWebSocketHandler:
    """Test WebSocketHandler class"""
    
    @pytest.mark.asyncio
    async def test_websocket_handler_creation(self):
        """Test creating WebSocketHandler"""
        mock_manager = Mock()
        mock_auth = Mock()
        
        handler = WebSocketHandler(mock_manager, mock_auth)
        
        assert handler.event_manager is mock_manager
        assert handler.auth_service is mock_auth
    
    def test_handler_message_routing(self):
        """Test message type routing"""
        mock_manager = Mock()
        mock_auth = Mock()
        
        handler = WebSocketHandler(mock_manager, mock_auth)
        
        # Verify handler has message routing methods
        assert hasattr(handler, '_handle_subscribe')
        assert hasattr(handler, '_handle_unsubscribe')
        assert hasattr(handler, '_handle_ping')
        assert hasattr(handler, '_handle_get_stats')
        assert hasattr(handler, '_handle_get_history')


# Fixtures for testing
@pytest.fixture
def event_manager():
    """Provide EventManager instance for tests"""
    return EventManager()


@pytest.fixture
def mock_db():
    """Provide mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def mock_websocket():
    """Provide mock WebSocket connection"""
    mock = AsyncMock()
    mock.accept = AsyncMock()
    mock.send_text = AsyncMock()
    mock.receive_text = AsyncMock()
    return mock
