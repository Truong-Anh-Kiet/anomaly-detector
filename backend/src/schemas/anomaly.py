"""Anomaly detection related Pydantic schemas"""

from enum import StrEnum

from pydantic import BaseModel, Field


class CauseEnum(StrEnum):
    """Anomaly cause classification"""
    STATISTICAL_SPIKE = "statistical_spike"
    ML_PATTERN_ANOMALY = "ml_pattern_anomaly"
    HYBRID_CONFIRMED = "hybrid_confirmed"
    SYSTEM_LEVEL_ANOMALY = "system_level_anomaly"
    NORMAL = "normal"


class ResultEnum(StrEnum):
    """Anomaly detection result"""
    NORMAL = "Normal"
    ANOMALY = "Anomaly"


class SeverityEnum(StrEnum):
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
    date_from: str | None = None
    date_to: str | None = None
    categories: list[str] | None = None
    severity: list[SeverityEnum] | None = None
    anomaly_type: list[CauseEnum] | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=500)


class TimeseriesPoint(BaseModel):
    """Single timeseries data point"""
    date: str
    amount: float
    is_anomaly: bool
    combined_score: float | None = None
    explanation: str | None = None


class TimeseriesResponse(BaseModel):
    """Timeseries data for charting"""
    category: str
    data: list[TimeseriesPoint]
