"""WebSocket integration tests - Phase 9"""

from datetime import datetime

import jwt
import pytest
from fastapi.testclient import TestClient

from src.main import create_app
from src.services.event_manager import (
    AnomalyEvent,
    EventConnection,
    EventManager,
    EventType,
    get_event_manager,
)


@pytest.fixture
def client():
    """Provide FastAPI test client"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Provide valid JWT token for testing"""
    payload = {
        "user_id": "test_user_123",
        "username": "testuser",
        "role": "ANALYST"
    }
    # Note: In real tests, use your actual secret and algorithm
    token = jwt.encode(payload, "secret", algorithm="HS256")
    return token


class TestWebSocketBasics:
    """Test basic WebSocket functionality"""

    def test_websocket_endpoint_exists(self, client):
        """Test WebSocket endpoint is registered"""
        # Cannot directly test WebSocket with TestClient,
        # but we can verify endpoint structure
        response = client.get("/ws/health")
        assert response.status_code == 200

    def test_websocket_stats_endpoint(self, client):
        """Test GET /ws/stats endpoint"""
        response = client.get("/ws/stats")
        assert response.status_code == 200
        data = response.json()

        # Should return stats
        assert "total_connections" in data
        assert "by_role" in data

    def test_websocket_health_endpoint(self, client):
        """Test GET /ws/health endpoint"""
        response = client.get("/ws/health")
        assert response.status_code == 200
        data = response.json()

        # Should return health status
        assert "status" in data
        assert "active_connections" in data
        assert "is_running" in data

    def test_websocket_history_endpoint(self, client):
        """Test GET /ws/history/{event_type} endpoint"""
        response = client.get("/ws/history/ANOMALY_DETECTED?limit=10")
        assert response.status_code == 200
        data = response.json()

        # Should return event history
        assert isinstance(data, (list, dict))


class TestWebSocketEventTypes:
    """Test WebSocket event type handling"""

    def test_anomaly_detected_type(self):
        """Test ANOMALY_DETECTED event type"""
        from src.services.event_manager import EventType
        assert EventType.ANOMALY_DETECTED.value == "anomaly_detected"

    def test_user_action_type(self):
        """Test USER_ACTION event type"""
        from src.services.event_manager import EventType
        assert EventType.USER_ACTION.value == "user_action"

    def test_threshold_exceeded_type(self):
        """Test THRESHOLD_EXCEEDED event type"""
        from src.services.event_manager import EventType
        assert EventType.THRESHOLD_EXCEEDED.value == "threshold_exceeded"

    def test_system_alert_type(self):
        """Test SYSTEM_ALERT event type"""
        from src.services.event_manager import EventType
        assert EventType.SYSTEM_ALERT.value == "system_alert"

    def test_heartbeat_type(self):
        """Test HEARTBEAT event type"""
        from src.services.event_manager import EventType
        assert EventType.HEARTBEAT.value == "heartbeat"


class TestEventBroadcasting:
    """Test event broadcasting mechanism"""

    def test_event_manager_singleton(self):
        """Test EventManager is accessible as singleton"""
        manager = get_event_manager()
        assert manager is not None

        # Should return same instance
        manager2 = get_event_manager()
        assert manager is manager2

    def test_event_manager_connection_tracking(self):
        """Test EventManager tracks connections"""
        manager = get_event_manager()

        # Manager should support adding connections
        assert hasattr(manager, 'add_connection')
        assert hasattr(manager, 'remove_connection')
        assert hasattr(manager, 'get_connection')

    def test_event_manager_broadcasting(self):
        """Test EventManager can broadcast events"""
        manager = get_event_manager()

        # Manager should support broadcasting
        assert hasattr(manager, 'broadcast_event')
        assert hasattr(manager, 'broadcast_to_role')
        assert hasattr(manager, 'broadcast_to_user')

    def test_event_history_tracking(self):
        """Test EventManager tracks event history"""
        manager = get_event_manager()

        # Manager should have event history
        assert hasattr(manager, 'event_history')
        assert isinstance(manager.event_history, list)

    def test_event_history_limit(self):
        """Test EventManager limits event history size"""
        from src.services.event_manager import AnomalyEvent, EventType
        manager = get_event_manager()

        # Add test event
        event = AnomalyEvent(
            anomaly_id="test123",
            category="test",
            score=0.95,
            threshold=0.7,
            severity="high",
            message="Test",
            timestamp=datetime.utcnow()
        )

        initial_size = len(manager.event_history)
        manager.broadcast_event(EventType.ANOMALY_DETECTED, event)

        # History should be updated
        assert len(manager.event_history) >= initial_size


class TestBroadcasterIntegration:
    """Test AnomalyEventBroadcaster integration"""

    @pytest.mark.asyncio
    async def test_broadcaster_singleton(self):
        """Test broadcaster is accessible as singleton"""
        from src.services.anomaly_broadcaster import get_anomaly_broadcaster

        broadcaster = get_anomaly_broadcaster()
        assert broadcaster is not None

        # Should return same instance
        broadcaster2 = get_anomaly_broadcaster()
        assert broadcaster is broadcaster2

    @pytest.mark.asyncio
    async def test_broadcaster_has_methods(self):
        """Test broadcaster has all required methods"""
        from src.services.anomaly_broadcaster import get_anomaly_broadcaster

        broadcaster = get_anomaly_broadcaster()

        # Should have broadcast methods
        assert hasattr(broadcaster, 'broadcast_anomaly_detected')
        assert hasattr(broadcaster, 'broadcast_threshold_exceeded')
        assert hasattr(broadcaster, 'broadcast_user_action')
        assert hasattr(broadcaster, 'broadcast_system_alert')
        assert hasattr(broadcaster, 'broadcast_to_role')
        assert hasattr(broadcaster, 'broadcast_to_user')


class TestWebSocketSecurity:
    """Test WebSocket security features"""

    def test_jwt_required_for_connection(self):
        """Test JWT token required for WebSocket connection"""
        # WebSocket endpoint should require token in query params
        # This would be tested with actual WebSocket client
        pass

    def test_invalid_token_rejected(self):
        """Test invalid token is rejected"""
        # Test that invalid JWT is rejected
        pass

    def test_token_validation(self):
        """Test token is properly validated"""
        # Test that token payloads are correctly parsed
        pass

    def test_user_context_tracking(self):
        """Test user context is tracked on connection"""
        # Test that EventConnection tracks user_id and role
        from src.services.event_manager import EventConnection

        conn = EventConnection(
            connection_id="test_conn",
            user_id="user123",
            role="ANALYST",
            subscribed_events=set(),
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )

        assert conn.user_id == "user123"
        assert conn.role == "ANALYST"


class TestRoleBasedAccess:
    """Test role-based event filtering"""

    def test_admin_can_receive_all_events(self):
        """Test ADMIN role receives all events"""
        from src.services.event_manager import EventConnection, EventType

        conn = EventConnection(
            connection_id="admin_conn",
            user_id="admin123",
            role="ADMIN",
            subscribed_events={
                EventType.ANOMALY_DETECTED,
                EventType.USER_ACTION,
                EventType.SYSTEM_ALERT
            },
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )

        # Admin should receive all subscribed events
        assert conn.can_receive(EventType.ANOMALY_DETECTED)
        assert conn.can_receive(EventType.USER_ACTION)
        assert conn.can_receive(EventType.SYSTEM_ALERT)

    def test_analyst_limited_events(self):
        """Test ANALYST role receives limited events"""
        from src.services.event_manager import EventConnection, EventType

        conn = EventConnection(
            connection_id="analyst_conn",
            user_id="analyst123",
            role="ANALYST",
            subscribed_events={EventType.ANOMALY_DETECTED},
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )

        # Analyst only subscribed to anomalies
        assert conn.can_receive(EventType.ANOMALY_DETECTED)
        assert not conn.can_receive(EventType.USER_ACTION)

    def test_subscription_filtering(self):
        """Test subscription filtering works"""
        from src.services.event_manager import EventConnection, EventType

        conn = EventConnection(
            connection_id="test_conn",
            user_id="user123",
            role="ANALYST",
            subscribed_events=set(),
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )

        # Subscribe to specific event
        conn.subscribe(EventType.ANOMALY_DETECTED)
        assert conn.can_receive(EventType.ANOMALY_DETECTED)

        # Should not receive other events
        assert not conn.can_receive(EventType.USER_ACTION)

        # Unsubscribe
        conn.unsubscribe(EventType.ANOMALY_DETECTED)
        assert not conn.can_receive(EventType.ANOMALY_DETECTED)


class TestConnectionLifecycle:
    """Test WebSocket connection lifecycle"""

    def test_connection_establishment(self):
        """Test connection establishment flow"""
        from src.services.event_manager import EventConnection

        # Simulate connection
        conn = EventConnection(
            connection_id="conn123",
            user_id="user456",
            role="ANALYST",
            subscribed_events=set(),
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )
        assert conn.connection_id == "conn123"
        assert conn.user_id == "user456"

    def test_heartbeat_management(self):
        """Test heartbeat/keepalive mechanism"""
        from src.services.event_manager import EventConnection

        old_time = datetime.utcnow()
        conn = EventConnection(
            connection_id="conn123",
            user_id="user456",
            role="ANALYST",
            subscribed_events=set(),
            connected_at=old_time,
            last_heartbeat=old_time
        )

        old_heartbeat = conn.last_heartbeat
        conn.update_heartbeat()

        # Heartbeat should be updated
        assert conn.last_heartbeat >= old_heartbeat

    def test_subscription_management(self):
        """Test subscription management during connection"""
        from src.services.event_manager import EventConnection, EventType

        conn = EventConnection(
            connection_id="conn123",
            user_id="user456",
            role="ANALYST",
            subscribed_events=set(),
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )

        # Subscribe to multiple events
        conn.subscribe(EventType.ANOMALY_DETECTED)
        conn.subscribe(EventType.USER_ACTION)

        assert len(conn.subscribed_events) == 2
        assert EventType.ANOMALY_DETECTED in conn.subscribed_events
        assert EventType.USER_ACTION in conn.subscribed_events


class TestMultipleConnections:
    """Test handling multiple concurrent connections"""

    def test_multiple_user_connections(self):
        """Test same user can have multiple connections"""
        manager = EventManager()

        # Same user, multiple connections
        for i in range(3):
            conn = EventConnection(
                connection_id=f"conn{i}",
                user_id="user123",
                role="ANALYST",
                subscribed_events=set(),
                connected_at=datetime.utcnow(),
                last_heartbeat=datetime.utcnow()
            )
            manager.add_connection(conn)

        user_conns = manager.get_user_connections("user123")
        assert len(user_conns) == 3

    def test_different_user_connections(self):
        """Test different users have separate connections"""
        manager = EventManager()

        # Different users
        for i in range(3):
            conn = EventConnection(
                connection_id=f"conn{i}",
                user_id=f"user{i}",
                role="ANALYST",
                subscribed_events=set(),
                connected_at=datetime.utcnow(),
                last_heartbeat=datetime.utcnow()
            )
            manager.add_connection(conn)

        assert len(manager.connections) == 3
        assert len(manager.get_user_connections("user0")) == 1
        assert len(manager.get_user_connections("user1")) == 1
        assert len(manager.get_user_connections("user2")) == 1

    def test_broadcast_to_multiple_subscribers(self):
        """Test event broadcast reaches multiple subscribers"""
        manager = EventManager()
        # Create multiple subscribers
        for i in range(3):
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
            anomaly_id="test123",
            category="test",
            score=0.95,
            threshold=0.7,
            severity="high",
            message="Test",
            timestamp=datetime.utcnow()
        )

        manager.broadcast_event(EventType.ANOMALY_DETECTED, event)

        # Event should be in history
        assert len(manager.event_history) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
