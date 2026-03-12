"""
Phase 7 Integration Examples
How to integrate WebSocket event broadcasting with existing API endpoints
"""

# Example 1: Broadcasting anomaly detection
# ==========================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.dependencies import get_db, get_current_user
from src.models import Anomaly, User
from src.services.anomaly_broadcaster import get_anomaly_broadcaster

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.post("/detect")
async def detect_anomaly(
    anomaly_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Detect anomaly and broadcast event
    """
    # Create and save anomaly
    anomaly = Anomaly(**anomaly_data)
    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)
    
    # Broadcast the detection event
    broadcaster = get_anomaly_broadcaster()
    await broadcaster.broadcast_anomaly_detected(anomaly, db)
    
    # Log user action
    await broadcaster.broadcast_user_action(
        user_id=current_user.user_id,
        action="view_anomaly",
        resource_type="anomaly",
        resource_id=anomaly.anomaly_id
    )
    
    return {"status": "created", "anomaly_id": anomaly.anomaly_id}


# Example 2: Broadcasting status update
# ======================================

@router.patch("/{anomaly_id}/status")
async def update_anomaly_status(
    anomaly_id: str,
    new_status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update anomaly status and broadcast change
    """
    anomaly = db.query(Anomaly).filter(Anomaly.anomaly_id == anomaly_id).first()
    
    old_status = anomaly.status
    anomaly.status = new_status
    db.commit()
    
    # Broadcast user action
    broadcaster = get_anomaly_broadcaster()
    await broadcaster.broadcast_user_action(
        user_id=current_user.user_id,
        action="update_status",
        resource_type="anomaly",
        resource_id=anomaly_id,
        details={
            "old_status": old_status,
            "new_status": new_status
        }
    )
    
    return {
        "status": "updated",
        "anomaly_id": anomaly_id,
        "new_status": new_status
    }


# Example 3: Broadcasting threshold changes
# ==========================================

@router.put("/thresholds/{category}")
async def update_threshold(
    category: str,
    new_value: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update threshold and broadcast change
    """
    # Update threshold in database
    # (assuming ThresholdConfig model exists)
    
    broadcaster = get_anomaly_broadcaster()
    
    # Broadcast threshold update
    await broadcaster.broadcast_user_action(
        user_id=current_user.user_id,
        action="update_threshold",
        resource_type="threshold",
        resource_id=category,
        details={"new_value": new_value}
    )
    
    # Optionally broadcast alert to admins
    if new_value < 0.5:
        await broadcaster.broadcast_system_alert(
            alert_type="low_threshold",
            title=f"Low Threshold Alert",
            message=f"Threshold for {category} is now {new_value:.2f}",
            severity="warning"
        )
    
    return {
        "status": "updated",
        "category": category,
        "new_value": new_value
    }


# Example 4: Broadcasting export action
# ======================================

@router.get("/export")
async def export_anomalies(
    format: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export anomalies and broadcast action
    """
    # Generate export file
    # (implementation details omitted)
    
    broadcaster = get_anomaly_broadcaster()
    await broadcaster.broadcast_user_action(
        user_id=current_user.user_id,
        action="export_data",
        resource_type="anomaly",
        details={"format": format}
    )
    
    return {
        "status": "exported",
        "format": format,
        "file": f"anomalies_export_{format}.{format}"
    }


# Example 5: Broadcasting system alerts
# ======================================

@router.get("/health/check")
async def health_check():
    """
    Perform health check and broadcast alerts if issues found
    """
    import time
    
    broadcaster = get_anomaly_broadcaster()
    
    # Simulate health check
    issues = []
    
    # Check database connection time
    start = time.time()
    # db query here
    query_time = time.time() - start
    
    if query_time > 1.0:
        issues.append("slow_database")
        await broadcaster.broadcast_system_alert(
            alert_type="slow_database",
            title="Database Performance Issue",
            message=f"Database query took {query_time:.2f}s",
            severity="warning"
        )
    
    # Check available connections
    if True:  # Check some metric
        await broadcaster.broadcast_system_alert(
            alert_type="system_status",
            title="System Status Good",
            message="All systems operational",
            severity="success"
        )
    
    return {
        "status": "healthy",
        "issues": issues,
        "query_time_ms": query_time * 1000
    }


# Example 6: Using event subscriptions
# ======================================

from src.services.event_manager import EventType, get_event_manager

def setup_event_handlers():
    """
    Register handlers for specific event types
    This should be called during application startup
    """
    event_manager = get_event_manager()
    
    def handle_anomaly_event(event: dict):
        """Handle when anomaly is detected"""
        print(f"Anomaly handler: {event}")
        # Could persist to special database
        # Could trigger automated responses
        # Could update dashboards
    
    def handle_threshold_event(event: dict):
        """Handle when threshold is exceeded"""
        print(f"Threshold handler: {event}")
        # Could escalate alert
        # Could trigger preventive actions
    
    def handle_user_action(event: dict):
        """Handle user action for audit trail"""
        print(f"Audit handler: {event}")
        # Could store in audit database
        # Could trigger compliance checks
    
    # Register handlers
    event_manager.register_handler(EventType.ANOMALY_DETECTED, handle_anomaly_event)
    event_manager.register_handler(EventType.THRESHOLD_EXCEEDED, handle_threshold_event)
    event_manager.register_handler(EventType.USER_ACTION, handle_user_action)


# Example 7: Broadcasting to specific roles
# ===========================================

@router.post("/alert/admin-only")
async def send_admin_alert(
    message: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send alert to admin users only
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    broadcaster = get_anomaly_broadcaster()
    
    event_dict = {
        "type": EventType.SYSTEM_ALERT.value,
        "title": "Admin Alert",
        "message": message
    }
    
    await broadcaster.broadcast_to_role(
        role="admin",
        event_dict=event_dict,
        event_type=EventType.SYSTEM_ALERT
    )
    
    return {"status": "alert_sent", "recipients": "admins"}


# Example 8: Broadcasting to specific user
# ==========================================

@router.post("/notify/{user_id}")
async def notify_user(
    user_id: str,
    notification: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send notification to specific user
    """
    broadcaster = get_anomaly_broadcaster()
    
    event_dict = {
        "type": EventType.USER_ACTION.value,
        "title": notification.get("title"),
        "message": notification.get("message")
    }
    
    await broadcaster.broadcast_to_user(
        user_id=user_id,
        event_dict=event_dict,
        event_type=EventType.USER_ACTION
    )
    
    return {
        "status": "notification_sent",
        "user_id": user_id
    }


"""
Integration Checklist:

1. Import broadcaster in each endpoint module:
   from src.services.anomaly_broadcaster import get_anomaly_broadcaster

2. Call broadcaster methods after database commits:
   await broadcaster.broadcast_anomaly_detected(anomaly, db)

3. Log user actions for audit trail:
   await broadcaster.broadcast_user_action(
       user_id=current_user.user_id,
       action="action_name",
       resource_type="resource",
       resource_id="id"
   )

4. Send alerts for important system events:
   await broadcaster.broadcast_system_alert(
       alert_type="type",
       title="Title",
       message="Message",
       severity="warning"
   )

5. Test with frontend WebSocket client:
   - Connect to ws://localhost:8000/ws?token=TOKEN
   - Subscribe to events
   - Trigger actions to see broadcasts

6. Monitor with REST endpoints:
   - GET /ws/stats - Connection statistics
   - GET /ws/history/{event_type} - Event history
   - GET /ws/health - System health
"""
