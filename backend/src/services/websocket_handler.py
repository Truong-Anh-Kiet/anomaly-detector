"""
WebSocket Endpoint Handler
Handles WebSocket connections and message routing
"""

import logging
import uuid
from datetime import datetime

from fastapi import HTTPException, WebSocket, status
from sqlalchemy.orm import Session

from src.services.auth_service import AuthService
from src.services.event_manager import (
    EventConnection,
    EventManager,
    EventType,
    get_event_manager,
)

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """Handles WebSocket connections and message routing"""

    def __init__(self, event_manager: EventManager, auth_service: AuthService):
        self.event_manager = event_manager
        self.auth_service = auth_service
        self.subscribed_event_types = {
            EventType.ANOMALY_DETECTED,
            EventType.THRESHOLD_EXCEEDED,
            EventType.USER_ACTION,
            EventType.SYSTEM_ALERT,
            EventType.HEARTBEAT,
        }

    async def connect(self, websocket: WebSocket, db: Session) -> EventConnection:
        """
        Establish WebSocket connection and authenticate

        Args:
            websocket: FastAPI WebSocket
            db: Database session

        Returns:
            EventConnection object

        Raises:
            HTTPException: If authentication fails
        """
        await websocket.accept()

        try:
            # Get auth token from query params
            token = websocket.query_params.get("token")
            if not token:
                await websocket.send_json({
                    "type": "error",
                    "message": "Authentication token required"
                })
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token required"
                )

            # Verify token and get user
            user = self.auth_service.verify_token(token, db)
            if not user:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid or expired token"
                })
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )

            # Create event connection
            connection_id = str(uuid.uuid4())
            connection = EventConnection(
                connection_id=connection_id,
                user_id=user.user_id,
                role=user.role.value if hasattr(user.role, 'value') else str(user.role)
            )

            # Subscribe to default events
            for event_type in self.subscribed_event_types:
                connection.subscribe(event_type)

            # Add to manager
            self.event_manager.add_connection(connection)

            # Send connection confirmation
            await websocket.send_json({
                "type": EventType.CONNECTION_ESTABLISHED.value,
                "connection_id": connection_id,
                "user_id": user.user_id,
                "username": user.username,
                "role": connection.role,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Connected to real-time event system"
            })

            logger.info(f"User {user.username} connected via WebSocket: {connection_id}")
            return connection

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during WebSocket connect: {e}")
            await websocket.close(code=status.WS_1011_SERVER_ERROR)
            raise

    async def disconnect(self, connection_id: str):
        """
        Disconnect WebSocket connection

        Args:
            connection_id: ID of connection to disconnect
        """
        connection = self.event_manager.get_connection(connection_id)
        if connection:
            self.event_manager.remove_connection(connection_id)
            logger.info(f"User {connection.user_id} disconnected: {connection_id}")

    async def handle_message(
        self,
        websocket: WebSocket,
        connection_id: str,
        message: dict
    ) -> dict:
        """
        Handle incoming WebSocket message

        Args:
            websocket: WebSocket connection
            connection_id: ID of the connection
            message: Parsed JSON message

        Returns:
            Response to send back
        """
        try:
            message_type = message.get("type", "unknown")
            payload = message.get("payload", {})

            connection = self.event_manager.get_connection(connection_id)
            if not connection:
                return {
                    "type": "error",
                    "message": "Connection not found"
                }

            # Handle different message types
            if message_type == "subscribe":
                return await self._handle_subscribe(connection, payload)

            elif message_type == "unsubscribe":
                return await self._handle_unsubscribe(connection, payload)

            elif message_type == "ping":
                return await self._handle_ping(connection)

            elif message_type == "get_stats":
                return await self._handle_get_stats(connection)

            elif message_type == "get_history":
                return await self._handle_get_history(payload)

            else:
                logger.warning(f"Unknown message type: {message_type}")
                return {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return {
                "type": "error",
                "message": str(e)
            }

    async def _handle_subscribe(self, connection: EventConnection, payload: dict) -> dict:
        """Handle subscribe request"""
        event_type = payload.get("event_type")

        try:
            event_enum = EventType(event_type)
            connection.subscribe(event_enum)
            return {
                "type": "subscribed",
                "event_type": event_type,
                "message": f"Subscribed to {event_type}"
            }
        except ValueError:
            return {
                "type": "error",
                "message": f"Invalid event type: {event_type}"
            }

    async def _handle_unsubscribe(self, connection: EventConnection, payload: dict) -> dict:
        """Handle unsubscribe request"""
        event_type = payload.get("event_type")

        try:
            event_enum = EventType(event_type)
            connection.unsubscribe(event_enum)
            return {
                "type": "unsubscribed",
                "event_type": event_type,
                "message": f"Unsubscribed from {event_type}"
            }
        except ValueError:
            return {
                "type": "error",
                "message": f"Invalid event type: {event_type}"
            }

    async def _handle_ping(self, connection: EventConnection) -> dict:
        """Handle ping (heartbeat) request"""
        connection.update_heartbeat()
        return {
            "type": EventType.HEARTBEAT.value,
            "message": "pong",
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _handle_get_stats(self, connection: EventConnection) -> dict:
        """Handle stats request"""
        stats = self.event_manager.get_connection_stats()
        return {
            "type": "stats",
            "data": stats,
            "user_connection_id": connection.connection_id
        }

    async def _handle_get_history(self, payload: dict) -> dict:
        """Handle history request"""
        event_type = payload.get("event_type")
        limit = payload.get("limit", 50)

        if event_type:
            history = [
                e for e in self.event_manager.event_history
                if e.get("event_type") == event_type
            ][-limit:]
        else:
            history = self.event_manager.event_history[-limit:]

        return {
            "type": "history",
            "count": len(history),
            "data": history
        }

    async def broadcast_event_to_subscribers(
        self,
        connection: EventConnection,
        event: dict
    ):
        """Broadcast event to all subscribed connections"""
        event_type = event.get("event_type")

        # Find all connections that should receive this event
        if event_type:
            recipients = [
                conn for conn in self.event_manager.connections.values()
                if conn.can_receive(EventType(event_type))
            ]
        else:
            recipients = list(self.event_manager.connections.values())

        logger.info(f"Broadcasting event to {len(recipients)} connections: {event_type}")
        return recipients


# Create global handler instance
ws_handler: WebSocketHandler | None = None


def get_ws_handler(auth_service: AuthService) -> WebSocketHandler:
    """Get or create WebSocket handler"""
    global ws_handler
    if ws_handler is None:
        ws_handler = WebSocketHandler(get_event_manager(), auth_service)
    return ws_handler
