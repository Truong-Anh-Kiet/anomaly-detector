"""Anomaly detection API endpoints with WebSocket broadcast integration"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import logging
from datetime import datetime, timedelta

from src.database import get_db
from src.schemas.anomaly import AnomalyListItem, AnomalyDetail
from src.models.anomaly_detection import AnomalyDetectionResult
from src.models.transaction import Transaction
from src.services.anomaly_detector import AnomalyDetectionService
from src.services.anomaly_broadcaster import get_anomaly_broadcaster
from src.ml.anomaly_model import AnomalyModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/anomalies", tags=["anomalies"])

# Initialize ML model for anomaly detection
_model = None

def get_anomaly_model():
    """Get or initialize anomaly detection model"""
    global _model
    if _model is None:
        _model = AnomalyModel()
    return _model


@router.post("/detect")
async def detect_anomalies(
    db: Session = Depends(get_db),
) -> dict:
    """
    Detect anomalies in recent transactions.
    
    This endpoint:
    1. Fetches recent transactions
    2. Runs anomaly detection
    3. Saves results to database
    4. Broadcasts events to WebSocket subscribers
    
    Returns:
        - detected_count: Number of anomalies detected
        - processed_count: Total transactions processed
        - anomalies: List of detected anomalies
    """
    try:
        # Get broadcaster and model
        broadcaster = get_anomaly_broadcaster()
        model = get_anomaly_model()
        detector = AnomalyDetectionService(model)
        
        # Fetch recent transactions (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_txns = db.query(Transaction).filter(
            Transaction.date >= seven_days_ago
        ).all()
        
        if not recent_txns:
            return {
                "status": "success",
                "detected_count": 0,
                "processed_count": 0,
                "anomalies": [],
                "message": "No transactions found in the specified period"
            }
        
        # Run anomaly detection
        results = detector.detect_anomalies(
            db=db,
            transactions=recent_txns,
            model_version="v1.0"
        )
        
        # Filter and broadcast anomalies
        detected_anomalies = [
            (txn, result) for txn, result in results 
            if result.result.value == "Anomaly"
        ]
        
        anomaly_list = []
        for txn, result in detected_anomalies:
            # Broadcast each anomaly to WebSocket subscribers
            await broadcaster.broadcast_anomaly_detected(result, db)
            
            anomaly_list.append({
                "detection_id": result.detection_id,
                "transaction_id": result.transaction_id,
                "category": txn.category,
                "amount": txn.amount,
                "combined_score": result.combined_score,
                "severity": "high" if result.combined_score >= 0.8 else (
                    "medium" if result.combined_score >= 0.6 else "low"
                ),
                "cause": result.cause.value
            })
        
        logger.info(
            f"Anomaly detection completed: {len(detected_anomalies)} anomalies "
            f"detected from {len(recent_txns)} transactions"
        )
        
        return {
            "status": "success",
            "detected_count": len(detected_anomalies),
            "processed_count": len(recent_txns),
            "anomalies": anomaly_list,
            "message": f"Detected {len(detected_anomalies)} anomalies, broadcasted to subscribers"
        }
        
    except Exception as e:
        logger.error(f"Error during anomaly detection: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")


@router.get("", response_model=dict)
async def list_anomalies(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    category: str = Query(None),
    severity: str = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    """
    List detected anomalies with optional filtering.
    
    Query Parameters:
    - skip: Number of results to skip (pagination)
    - limit: Number of results to return (max 500)
    - category: Filter by transaction category
    - severity: Filter by severity (low, medium, high)
    
    Returns:
        - total: Total anomalies matching filters
        - count: Number of anomalies in this page
        - anomalies: List of anomalies
    """
    try:
        query = db.query(AnomalyDetectionResult).filter(
            AnomalyDetectionResult.result == "Anomaly"
        )
        
        # Apply filters
        if category:
            from src.models.transaction import Transaction
            txn_ids = [t.transaction_id for t in db.query(Transaction).filter(
                Transaction.category == category
            ).all()]
            query = query.filter(AnomalyDetectionResult.transaction_id.in_(txn_ids))
        
        if severity:
            score_min = 0.6 if severity == "medium" else (0.8 if severity == "high" else 0)
            score_max = 0.8 if severity == "medium" else (1.0 if severity == "high" else 0.6)
            query = query.filter(
                AnomalyDetectionResult.combined_score >= score_min,
                AnomalyDetectionResult.combined_score < score_max
            )
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        results = query.order_by(
            AnomalyDetectionResult.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        # Convert to response format
        anomalies = []
        for result in results:
            txn = db.query(Transaction).filter(
                Transaction.transaction_id == result.transaction_id
            ).first()
            
            if txn:
                anomalies.append({
                    "detection_id": result.detection_id,
                    "transaction_id": result.transaction_id,
                    "date": txn.date.isoformat() if txn.date else None,
                    "category": txn.category,
                    "amount": txn.amount,
                    "stats_score": result.stats_score,
                    "ml_score": result.ml_score,
                    "combined_score": result.combined_score,
                    "severity": "high" if result.combined_score >= 0.8 else (
                        "medium" if result.combined_score >= 0.6 else "low"
                    ),
                    "cause": result.cause.value,
                    "explanation": result.base_explanation,
                    "created_at": result.created_at.isoformat()
                })
        
        return {
            "status": "success",
            "total": total,
            "count": len(anomalies),
            "skip": skip,
            "limit": limit,
            "anomalies": anomalies
        }
        
    except Exception as e:
        logger.error(f"Error listing anomalies: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list anomalies: {str(e)}")


@router.get("/{detection_id}", response_model=dict)
async def get_anomaly_detail(
    detection_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get detailed information about a specific anomaly.
    
    Returns:
        - detection_id: Anomaly detection ID
        - transaction_id: Associated transaction ID
        - category: Transaction category
        - amount: Transaction amount
        - stats_score: Statistical detection score
        - ml_score: ML detection score
        - combined_score: Combined hybrid score
        - severity: Severity level
        - cause: Anomaly cause
        - explanation: Human-readable explanation
        - advice: Recommended action
        - model_version: ML model version used
        - created_at: Detection timestamp
    """
    try:
        result = db.query(AnomalyDetectionResult).filter(
            AnomalyDetectionResult.detection_id == detection_id
        ).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="Anomaly not found")
        
        txn = db.query(Transaction).filter(
            Transaction.transaction_id == result.transaction_id
        ).first()
        
        return {
            "status": "success",
            "detection_id": result.detection_id,
            "transaction_id": result.transaction_id,
            "date": txn.date.isoformat() if txn and txn.date else None,
            "category": txn.category if txn else None,
            "amount": txn.amount if txn else None,
            "stats_score": result.stats_score,
            "ml_score": result.ml_score,
            "combined_score": result.combined_score,
            "severity": "high" if result.combined_score >= 0.8 else (
                "medium" if result.combined_score >= 0.6 else "low"
            ),
            "cause": result.cause.value,
            "result": result.result.value,
            "explanation": result.base_explanation,
            "advice": result.advice,
            "model_version": result.model_version,
            "created_at": result.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting anomaly detail: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get anomaly detail: {str(e)}")
