"""Anomaly detection related Pydantic schemas"""

from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional, List


class CauseEnum(str, Enum):
    """Anomaly cause classification"""
    STATISTICAL_SPIKE = "statistical_spike"
    ML_PATTERN_ANOMALY = "ml_pattern_anomaly"
    HYBRID_CONFIRMED = "hybrid_confirmed"
    SYSTEM_LEVEL_ANOMALY = "system_level_anomaly"
    NORMAL = "normal"


class ResultEnum(str, Enum):
    """Anomaly detection result"""
    NORMAL = "Normal"
    ANOMALY = "Anomaly"


class SeverityEnum(str, Enum):
    """Anomaly severity level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AnomalyListItem(BaseModel):
    """Anomaly list item response (brief)"""
    detection_id: str
    transaction_id: str
    date: str
    category: str
    amount: float
    stats_score: float
    ml_score: float
    combined_score: float
    result: ResultEnum
    cause: CauseEnum
    severity: SeverityEnum
    brief_explanation: str

    class Config:
        from_attributes = True


class AnomalyDetail(BaseModel):
    """Anomaly detail response (full explanation)"""
    detection_id: str
    transaction_id: str
    date: str
    category: str
    amount: float
    stats_score: float
    ml_score: float
    combined_score: float
    result: ResultEnum
    cause: CauseEnum
    severity: SeverityEnum
    base_explanation: str
    advice: str
    model_version: str
    created_at: str

    class Config:
        from_attributes = True


class AnomalyFilterParams(BaseModel):
    """Query parameters for anomaly filtering"""
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    categories: Optional[List[str]] = None
    severity: Optional[List[SeverityEnum]] = None
    anomaly_type: Optional[List[CauseEnum]] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=500)


class TimeseriesPoint(BaseModel):
    """Single timeseries data point"""
    date: str
    amount: float
    is_anomaly: bool
    combined_score: Optional[float] = None
    explanation: Optional[str] = None


class TimeseriesResponse(BaseModel):
    """Timeseries data for charting"""
    category: str
    data: List[TimeseriesPoint]
