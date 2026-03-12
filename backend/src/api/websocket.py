"""
WebSocket Routes
Real-time event streaming endpoints
"""

import json
import logging

import pandas as pd
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from src.dependencies import get_auth_service, get_db
from src.services.auth_service import AuthService
from src.services.event_manager import EventType, get_event_manager
from src.services.websocket_handler import get_ws_handler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db), # noqa: B008
    auth_service: AuthService = Depends(get_auth_service), # noqa: B008
):
    """
    WebSocket endpoint for real-time event streaming

    Query Parameters:
        token (str): JWT authentication token

    Client Message Format:
        {
            "type": "subscribe|unsubscribe|ping|get_stats|get_history",
            "payload": {...}
        }

    Server Response Format:
        {
            "type": "event_type|subscribed|unsubscribed|error|...",
            "data": {...},
            "timestamp": "2026-03-12T..."
        }
    """
    connection = None

    try:
        # Initialize handler
        handler = get_ws_handler(auth_service)

        # Authenticate and establish connection
        connection = await handler.connect(websocket, db)

        # Main message loop
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
                continue

            # Route message to handler
            response = await handler.handle_message(
                websocket,
                connection.connection_id,
                message
            )

            # Send response
            await websocket.send_json(response)

    except WebSocketDisconnect:
        if connection:
            await handler.disconnect(connection.connection_id)
        logger.info(f"Client disconnected: {connection.connection_id if connection else 'unknown'}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if connection:
            await handler.disconnect(connection.connection_id)
        try:
            await websocket.close(code=status.WS_1011_SERVER_ERROR)
        except Exception:
            pass


@router.get("/stats", tags=["monitoring"])
async def get_websocket_stats(
    event_manager = Depends(get_event_manager), # noqa: B008
):
    """
    Get WebSocket connection statistics

    Returns:
        {
            "total_connections": int,
            "by_role": {"admin": int, "analyst": int, ...},
            "history_size": int,
            "timestamp": "2026-03-12T..."
        }
    """
    stats = event_manager.get_connection_stats()
    return {
        "data": stats,
        "timestamp": str(pd.Timestamp.now(tz='UTC')) if 'pd' in globals() else None
    }


@router.get("/history/{event_type}", tags=["monitoring"])
async def get_event_history(
    event_type: str,
    limit: int = 50,
    event_manager = Depends(get_event_manager), # noqa: B008
):
    """
    Get historical events for a specific type

    Args:
        event_type (str): Type of event (anomaly_detected, threshold_exceeded, etc.)
        limit (int): Maximum number of events to return (default: 50)

    Returns:
        {
            "event_type": "anomaly_detected",
            "count": int,
            "events": [...]
        }
    """
    try:
        # Validate event type
        EventType(event_type)
    except ValueError:
        return {
            "error": f"Invalid event type: {event_type}",
            "valid_types": [e.value for e in EventType]
        }

    history = [
        e for e in event_manager.event_history
        if e.get("event_type") == event_type
    ][-limit:]

    return {
        "event_type": event_type,
        "count": len(history),
        "limit": limit,
        "events": history
    }


@router.get("/health", tags=["monitoring"])
async def websocket_health(
    event_manager = Depends(get_event_manager), # noqa: B008
):
    """
    Check WebSocket system health

    Returns:
        {
            "status": "healthy",
            "connections": int,
            "events_in_history": int
        }
    """
    stats = event_manager.get_connection_stats()
    return {
        "status": "healthy" if stats["total_connections"] >= 0 else "degraded",
        "active_connections": stats["total_connections"],
        "events_in_history": stats["history_size"],
        "is_running": True
    }
