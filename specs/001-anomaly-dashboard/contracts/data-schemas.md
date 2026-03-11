# Data Schemas Contract

**Feature**: Anomaly Detection Dashboard  
**Contract Version**: 1.0.0  
**Date**: 2026-03-11  
**Format**: JSON Schema (with Pydantic examples for Python)

---

## Authentication Schemas

### LoginRequest

**Purpose**: Credentials for user authentication

**JSON Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "LoginRequest",
  "type": "object",
  "properties": {
    "username": {
      "type": "string",
      "minLength": 3,
      "maxLength": 50,
      "pattern": "^[a-zA-Z0-9_]+$",
      "description": "Username; alphanumeric + underscore"
    },
    "password": {
      "type": "string",
      "minLength": 8,
      "maxLength": 255,
      "description": "Plain text password (sent over HTTPS)"
    }
  },
  "required": ["username", "password"],
  "additionalProperties": false
}
```

**Pydantic Model**:
```python
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=255)
    
    class Config:
        schema_extra = {
            "example": {
                "username": "analyst_john",
                "password": "SecureP@ssw0rd123"
            }
        }
```

---

### LoginResponse

**Purpose**: JWT tokens and user info after successful authentication

**JSON Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "LoginResponse",
  "type": "object",
  "properties": {
    "access_token": {
      "type": "string",
      "description": "JWT access token (15min expiry)"
    },
    "refresh_token": {
      "type": "string",
      "description": "JWT refresh token (7day expiry)"
    },
    "expires_in": {
      "type": "integer",
      "minimum": 1,
      "description": "Seconds until access_token expiration"
    },
    "user": {
      "$ref": "#/definitions/UserInfo"
    }
  },
  "required": ["access_token", "refresh_token", "expires_in", "user"],
  "additionalProperties": false
}
```

**Pydantic Model**:
```python
class UserInfo(BaseModel):
    user_id: str = Field(..., description="UUID of user")
    username: str
    role: Literal["ADMIN", "MANAGER", "ANALYST"]
    assigned_categories: list[str] = Field(default_factory=list, description="For ANALYST role only")

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int = Field(..., ge=1)
    user: UserInfo
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "expires_in": 900,
                "user": {
                    "user_id": "550e8400-e29b-41d4-a716-446655440001",
                    "username": "analyst_john",
                    "role": "ANALYST",
                    "assigned_categories": ["Fast Food", "Restaurant"]
                }
            }
        }
```

---

## Anomaly Schemas

### AnomalyListItem

**Purpose**: Single anomaly in list response

**Pydantic Model**:
```python
class AnomalyListItem(BaseModel):
    detection_id: str = Field(..., description="UUID of detection record")
    transaction_id: str = Field(..., description="UUID of transaction")
    date: str = Field(..., description="Transaction date (YYYY-MM-DD)")
    category: str = Field(..., description="Financial category")
    amount: float = Field(..., gt=0, description="Transaction amount")
    combined_score: float = Field(..., ge=0, le=1, description="0-1 anomaly score")
    result: Literal["Normal", "Anomaly"] = Field(..., description="Classification")
    cause: Literal[
        "sudden_spike", "sudden_drop", "sharp_change", 
        "gradual_drift", "high_volatility_drift", "normal"
    ]
    severity: Literal["low", "medium", "high"] = Field(
        ..., 
        description="Derived from combined_score: score > 0.9 = high, 0.7-0.9 = medium, < 0.7 = low"
    )
    stats_score: float = Field(..., ge=0, le=1, description="Statistical anomaly score")
    ml_score: float = Field(..., ge=0, le=1, description="ML model anomaly score")
    explanation: str = Field(..., description="Human-readable anomaly explanation")
    model_version: str = Field(..., description="Model version that generated result")
    created_at: str = Field(..., description="ISO-8601 timestamp of detection")
    
    class Config:
        schema_extra = {
            "example": {
                "detection_id": "det-001",
                "transaction_id": "txn-001",
                "date": "2026-03-10",
                "category": "Fast Food",
                "amount": 125.50,
                "combined_score": 0.9854,
                "result": "Anomaly",
                "cause": "sudden_spike",
                "severity": "high",
                "stats_score": 0.98,
                "ml_score": 0.99,
                "explanation": "Amount significantly exceeds historical fast food average (mean: $18.50, z-score: +12.3)",
                "model_version": "model_v1709164234_anomaly_forest.pkl",
                "created_at": "2026-03-10T14:30:22Z"
            }
        }
```

---

### AnomalyDetail

**Purpose**: Detailed anomaly with explanations and historical context

**Pydantic Model**:
```python
class StatsScoreDetail(BaseModel):
    z_score: float = Field(..., description="Raw Z-score from statistical analysis")
    score: float = Field(..., ge=0, le=1, description="Normalized 0-1 score")

class MLScoreDetail(BaseModel):
    anomaly_score: float = Field(..., description="Raw Isolation Forest anomaly score")
    score: float = Field(..., ge=0, le=1, description="Normalized 0-1 score")
    isolation_depth: int = Field(..., ge=0, description="Tree depth where anomaly detected")

class HistoricalContext(BaseModel):
    category_mean: float = Field(..., description="Average amount in category")
    category_std: float = Field(..., description="Standard deviation in category")
    category_max_30d: float = Field(..., description="Max amount in last 30 days")
    user_max_ever: float = Field(..., description="User's max transaction ever")

class SourceTransaction(BaseModel):
    date: str
    category: str
    amount: float
    source: str = Field(default=None, description="e.g., visa_credit_card, debit_card")

class AnomalyDetail(BaseModel):
    detection_id: str
    transaction_id: str
    date: str
    category: str
    amount: float
    combined_score: float = Field(..., ge=0, le=1)
    result: Literal["Normal", "Anomaly"]
    cause: str
    base_explanation: str = Field(..., description="Summary explanation")
    detailed_explanation: str = Field(..., description="Detailed technical explanation")
    advice: str = Field(..., description="Actionable recommendation")
    historical_context: HistoricalContext
    stats_score: StatsScoreDetail
    ml_score: MLScoreDetail
    model_version: str
    created_at: str
    source_transaction: SourceTransaction
    
    class Config:
        schema_extra = {
            "example": {
                "detection_id": "det-001",
                "transaction_id": "txn-001",
                "date": "2026-03-10",
                "category": "Fast Food",
                "amount": 125.50,
                "combined_score": 0.9854,
                "result": "Anomaly",
                "cause": "sudden_spike",
                "base_explanation": "Amount significantly exceeds historical fast food average",
                "detailed_explanation": "Z-score calculation: (125.50 - 18.50) / 8.3 = 12.89 (>3σ threshold). Isolation Forest confidence: 0.99. This transaction is an extreme outlier.",
                "advice": "Review transaction for fraud; compare with merchant profile and user behavior",
                "historical_context": {
                    "category_mean": 18.50,
                    "category_std": 8.30,
                    "category_max_30d": 55.25,
                    "user_max_ever": 98.50
                },
                "stats_score": {
                    "z_score": 12.89,
                    "score": 0.98
                },
                "ml_score": {
                    "anomaly_score": -0.8234,
                    "score": 0.99,
                    "isolation_depth": 5
                },
                "model_version": "model_v1709164234_anomaly_forest.pkl",
                "created_at": "2026-03-10T14:30:22Z",
                "source_transaction": {
                    "date": "2026-03-10",
                    "category": "Fast Food",
                    "amount": 125.50,
                    "source": "visa_credit_card"
                }
            }
        }
```

---

### AnomalyListResponse

**Purpose**: Paginated list of anomalies

**Pydantic Model**:
```python
class PaginationInfo(BaseModel):
    current_page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1, le=500)
    total_count: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)

class AnomalyListResponse(BaseModel):
    data: list[AnomalyListItem]
    pagination: PaginationInfo
    
    class Config:
        schema_extra = {
            "example": {
                "data": [...],
                "pagination": {
                    "current_page": 1,
                    "per_page": 20,
                    "total_count": 247,
                    "total_pages": 13
                }
            }
        }
```

---

## Category Schemas

### Category

**Purpose**: Financial transaction category

**Pydantic Model**:
```python
class Category(BaseModel):
    category_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=5, max_length=255)
    description: str = Field(default=None)
    
    class Config:
        schema_extra = {
            "example": {
                "category_id": 1,
                "name": "Average Fast Food format Check",
                "description": "Average transaction amount in fast food sector"
            }
        }

class CategoriesResponse(BaseModel):
    data: list[Category]
    total: int = Field(..., ge=0)
```

---

## Timeseries Schemas

### TimeseriesPoint

**Purpose**: Single day's aggregated anomaly data

**Pydantic Model**:
```python
class TimeseriesPoint(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")
    normal_count: int = Field(..., ge=0, description="Transaction count (not anomalies)")
    anomaly_count: int = Field(..., ge=0, description="Anomaly count")
    daily_total: float = Field(..., description="Sum of transaction amounts")
    daily_mean: float = Field(..., description="Average transaction amount")
    daily_max: float = Field(..., description="Highest transaction amount")

class TimeseriesSummary(BaseModel):
    total_transactions: int = Field(..., ge=0)
    total_anomalies: int = Field(..., ge=0)
    period_mean: float
    period_std: float

class TimeseriesResponse(BaseModel):
    category: str = Field(..., description="Financial category")
    data: list[TimeseriesPoint]
    summary: TimeseriesSummary
    
    class Config:
        schema_extra = {
            "example": {
                "category": "Fast Food",
                "data": [
                    {
                        "date": "2026-01-01",
                        "normal_count": 3,
                        "anomaly_count": 0,
                        "daily_total": 52.50,
                        "daily_mean": 17.50,
                        "daily_max": 25.00
                    }
                ],
                "summary": {
                    "total_transactions": 412,
                    "total_anomalies": 18,
                    "period_mean": 18.50,
                    "period_std": 8.30
                }
            }
        }
```

---

## Model Management Schemas

### ModelMetrics

**Purpose**: Model performance metrics

**Pydantic Model**:
```python
class ModelMetrics(BaseModel):
    precision: float = Field(..., ge=0, le=1)
    recall: float = Field(..., ge=0, le=1)
    f1_score: float = Field(..., ge=0, le=1)
    training_date: str = Field(..., description="YYYY-MM-DD")
    training_set_size: int = Field(..., ge=1)
    test_set_size: int = Field(..., ge=1)
    threshold: float = Field(..., ge=0, le=1, description="Decision threshold for anomaly classification")
    
    class Config:
        schema_extra = {
            "example": {
                "precision": 0.9524,
                "recall": 1.0,
                "f1_score": 0.9756,
                "training_date": "2026-03-11",
                "training_set_size": 600,
                "test_set_size": 100,
                "threshold": 0.914
            }
        }
```

### ModelUploadRequest

**Purpose**: Form data for model upload

**Note**: This is multipart/form-data, not JSON

**Fields**:
```
model_file: File (binary .pkl)
version_name: string
metrics: string (JSON serialized)
```

**Pydantic Model**:
```python
class ModelUploadRequest(BaseModel):
    version_name: str = Field(..., min_length=5, max_length=255, regex="^[a-zA-Z0-9_v.-]+$")
    metrics: ModelMetrics
    # model_file is handled by UploadFile from FastAPI
```

### ModelVersion

**Purpose**: Model version record

**Pydantic Model**:
```python
class ModelVersion(BaseModel):
    version_id: str = Field(..., description="UUID")
    version_name: str
    uploaded_by: str = Field(..., description="Username of uploader (usually admin)")
    uploaded_at: str = Field(..., description="ISO-8601 timestamp")
    is_active: bool
    metrics: ModelMetrics
    
    class Config:
        schema_extra = {
            "example": {
                "version_id": "ver-001",
                "version_name": "model_v1709164234_anomaly_forest.pkl",
                "uploaded_by": "admin_alice",
                "uploaded_at": "2026-03-05T08:00:00Z",
                "is_active": True,
                "metrics": {
                    "precision": 0.9234,
                    "recall": 0.9456,
                    "f1_score": 0.9344,
                    "training_date": "2026-03-05",
                    "training_set_size": 600,
                    "test_set_size": 100,
                    "threshold": 0.914
                }
            }
        }

class ModelListResponse(BaseModel):
    data: list[ModelVersion]
    total: int = Field(..., ge=0)
```

---

## Error Schemas

### ErrorDetail

**Purpose**: Standard error response

**Pydantic Model**:
```python
class ErrorDetail(BaseModel):
    error: str = Field(..., description="Human-readable error message")
    error_code: str = Field(..., regex="^[A-Z_]+_[0-9]{3}$", description="Machine-readable error code")
    details: dict = Field(default_factory=dict, description="Additional context")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "Invalid date_from format. Expected YYYY-MM-DD",
                "error_code": "VALIDATION_001",
                "details": {
                    "field": "date_from",
                    "expected": "YYYY-MM-DD",
                    "received": "03/10/2026"
                }
            }
        }
```

---

## Query Parameter Schemas

### AnomalyFilterParams

**Purpose**: Standardized anomaly query parameters

**Pydantic Model**:
```python
from datetime import date
from typing import Optional

class AnomalyFilterParams(BaseModel):
    date_from: Optional[date] = Field(None, description="Start date for filter (default: 30 days ago)")
    date_to: Optional[date] = Field(None, description="End date for filter (default: today)")
    categories: Optional[str] = Field(None, description="Comma-separated category names")
    severity: Optional[str] = Field(None, description="Comma-separated: low,medium,high")
    anomaly_type: Optional[str] = Field(None, description="Comma-separated cause codes")
    page: int = Field(1, ge=1)
    per_page: int = Field(50, ge=1, le=500)
    sort_by: str = Field("created_at", regex="^(created_at|combined_score|date)$")
    sort_order: str = Field("desc", regex="^(asc|desc)$")
    
    @validator("date_from", "date_to", pre=True)
    def parse_dates(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "date_from": "2026-02-01",
                "date_to": "2026-03-10",
                "categories": "Fast Food,Restaurant",
                "severity": "high",
                "anomaly_type": "sudden_spike",
                "page": 1,
                "per_page": 20,
                "sort_by": "combined_score",
                "sort_order": "desc"
            }
        }
```

---

## Contract Status

✅ **Authentication schemas (login, refresh)**
✅ **Anomaly list + detail schemas**
✅ **Category schemas**
✅ **Timeseries schemas**
✅ **Model management schemas**
✅ **Error schemas**
✅ **Query parameter schemas**

**Ready for**: 
- Pydantic model code generation
- OpenAPI/Swagger spec generation
- Frontend TypeScript type generation
- Request/response validation

