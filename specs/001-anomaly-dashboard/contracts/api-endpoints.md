# API Endpoints Contract

**Feature**: Anomaly Detection Dashboard  
**Contract Version**: 1.0.0  
**Date**: 2026-03-11  
**Format**: RESTful JSON API  
**Authentication**: JWT Bearer Token  
**Base URL**: `http://localhost:8000/api` (dev) | `https://api.anomaly-detector.com/api` (prod)

---

## Authentication Endpoints

### POST /auth/login

**Description**: Authenticate user and issue JWT tokens

**Access**: Public (no auth required)

**Request**:
```json
{
  "username": "analyst_john",
  "password": "SecureP@ssw0rd123"
}
```

**Response** (200 OK):
```json
{
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
```

**Response** (401 Unauthorized):
```json
{
  "error": "Invalid credentials",
  "error_code": "AUTH_001"
}
```

**Token Details**:
- `access_token`: Valid for 15 minutes; sent in `Authorization: Bearer <token>` header
- `refresh_token`: Valid for 7 days; used to obtain new access_token without re-login
- `expires_in`: Seconds until access_token expiration

---

### POST /auth/refresh

**Description**: Obtain new access token using refresh token

**Access**: Public (presents refresh_token)

**Request**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 900
}
```

**Response** (401 Unauthorized):
```json
{
  "error": "Refresh token expired",
  "error_code": "AUTH_002"
}
```

---

## Anomaly Detection Endpoints

### GET /anomalies

**Description**: List anomalies with optional filtering

**Access**: ANALYST (own categories) | MANAGER (all) | ADMIN (all)

**Authorization**: Requires valid JWT access_token in `Authorization: Bearer` header

**Query Parameters**:

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| date_from | ISO-8601 date | No | 30 days ago | Filter start date (YYYY-MM-DD) |
| date_to | ISO-8601 date | No | Today | Filter end date (YYYY-MM-DD) |
| categories | CSV string | No | (all user categories) | e.g., "Fast Food,Restaurant" |
| severity | CSV string | No | (all) | Options: "low", "medium", "high" (mapped from score thresholds) |
| anomaly_type | CSV string | No | (all) | Options: "sudden_spike", "gradual_drift", "high_volatility_drift" |
| page | Integer | No | 1 | Pagination offset |
| per_page | Integer | No | 50 | Results per page (max 500) |
| sort_by | String | No | "created_at" | Options: "created_at", "combined_score", "date" |
| sort_order | String | No | "desc" | Options: "asc", "desc" |

**Example Request**:
```
GET /api/anomalies?date_from=2026-02-01&date_to=2026-03-10&categories=Fast%20Food,Restaurant&severity=high&page=1&per_page=20&sort_by=combined_score&sort_order=desc
```

**Response** (200 OK):
```json
{
  "data": [
    {
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
      "model_version": "model_v1709164234_anomaly_forest.pkl"
    },
    {
      "detection_id": "det-002",
      "transaction_id": "txn-002",
      "date": "2026-03-09",
      "category": "Restaurant",
      "amount": 45.25,
      "combined_score": 0.7123,
      "result": "Anomaly",
      "cause": "sharp_change",
      "severity": "medium",
      "stats_score": 0.68,
      "ml_score": 0.73,
      "explanation": "Amount 20% higher than usual restaurant spending",
      "model_version": "model_v1709164234_anomaly_forest.pkl"
    }
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 20,
    "total_count": 247,
    "total_pages": 13
  }
}
```

**Response** (400 Bad Request):
```json
{
  "error": "Invalid date_from format. Expected YYYY-MM-DD",
  "error_code": "VALIDATION_001"
}
```

**Response** (403 Forbidden - ANALYST with category not assigned):
```json
{
  "error": "Analyst can only view assigned categories",
  "error_code": "AUTHZ_001"
}
```

**Performance Notes**:
- Target latency: <500ms (p95)
- Database will use composite index on (date, category, result)
- Large result sets aggregated for performance (e.g., 365+ days may be pre-aggregated hourly)

---

### GET /anomalies/{detection_id}

**Description**: Get detailed explanation for specific anomaly

**Access**: ANALYST (own categories) | MANAGER (all) | ADMIN (all)

**Path Parameters**:
- `detection_id` (UUID): Unique anomaly detection identifier

**Example Request**:
```
GET /api/anomalies/det-001
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "detection_id": "det-001",
  "transaction_id": "txn-001",
  "date": "2026-03-10",
  "category": "Fast Food",
  "amount": 125.50,
  "combined_score": 0.9854,
  "result": "Anomaly",
  "cause": "sudden_spike",
  "base_explanation": "Amount significantly exceeds historical fast food average",
  "detailed_explanation": "Z-score calculation: (125.50 - 18.50) / 8.3 = 12.89 (>3σ threshold). Isolation Forest confidence: 0.99. This transaction is an extreme outlier compared to normal fast food categories.",
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
```

**Response** (404 Not Found):
```json
{
  "error": "Detection not found",
  "error_code": "NOT_FOUND_001"
}
```

---

### GET /categories

**Description**: List all available transaction categories

**Access**: ANALYST | MANAGER | ADMIN (all authenticated users)

**Query Parameters**: None

**Example Request**:
```
GET /api/categories
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "data": [
    {
      "category_id": 1,
      "name": "Average Fast Food format Check",
      "description": "Average transaction amount in fast food sector"
    },
    {
      "category_id": 2,
      "name": "Average check in Restaurant format",
      "description": "Average check amount in restaurants"
    },
    {
      "category_id": 3,
      "name": "Average consumer loan application",
      "description": "Average consumer loan application amount"
    },
    {
      "category_id": 4,
      "name": "Average pension",
      "description": "Average pension payment"
    }
  ],
  "total": 4
}
```

---

### GET /timeseries/{category}

**Description**: Get historical time series data for charting (aggregated by day)

**Access**: ANALYST (own categories) | MANAGER (all) | ADMIN (all)

**Path Parameters**:
- `category` (string): Category name (URL-encoded)

**Query Parameters**:

| Parameter | Type | Required | Default |
|-----------|------|----------|---------|
| date_from | ISO-8601 | No | 90 days ago |
| date_to | ISO-8601 | No | Today |

**Example Request**:
```
GET /api/timeseries/Fast%20Food?date_from=2026-01-01&date_to=2026-03-10
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "category": "Fast Food",
  "data": [
    {
      "date": "2026-01-01",
      "normal_count": 3,
      "anomaly_count": 0,
      "daily_total": 52.50,
      "daily_mean": 17.50,
      "daily_max": 25.00
    },
    {
      "date": "2026-01-02",
      "normal_count": 5,
      "anomaly_count": 1,
      "daily_total": 98.75,
      "daily_mean": 16.46,
      "daily_max": 45.00
    },
    ...
    {
      "date": "2026-03-10",
      "normal_count": 2,
      "anomaly_count": 1,
      "daily_total": 145.75,
      "daily_mean": 48.58,
      "daily_max": 125.50
    }
  ],
  "summary": {
    "total_transactions": 412,
    "total_anomalies": 18,
    "period_mean": 18.50,
    "period_std": 8.30
  }
}
```

---

## Admin Endpoints

### POST /admin/retrain

**Description**: Upload new ML model version (admin only)

**Access**: ADMIN only

**Content-Type**: multipart/form-data

**Request Parts**:
- `model_file` (binary, required): `.pkl` file (joblib serialized Isolation Forest model)
- `version_name` (string, required): Semantic version identifier (e.g., "model_v1709200000_rf_v2")
- `metrics` (JSON, required): Training metrics (precision, recall, f1, training_date)

**Example Request**:
```bash
curl -X POST "http://localhost:8000/api/admin/retrain" \
  -H "Authorization: Bearer <token>" \
  -F "model_file=@model_v1709200000.pkl" \
  -F "version_name=model_v1709200000_rf_v2" \
  -F "metrics={\"precision\": 0.9524, \"recall\": 1.0, \"f1_score\": 0.9756, \"training_date\": \"2026-03-11\", \"training_set_size\": 600, \"test_set_size\": 100, \"threshold\": 0.914}"
```

**Response** (201 Created):
```json
{
  "version_id": "ver-123",
  "version_name": "model_v1709200000_rf_v2",
  "message": "Model uploaded. Ready to activate.",
  "uploaded_at": "2026-03-11T10:30:00Z",
  "metrics": {
    "precision": 0.9524,
    "recall": 1.0,
    "f1_score": 0.9756,
    "training_date": "2026-03-11",
    "threshold": 0.914
  },
  "is_active": false,
  "next_step": "POST /admin/activate-model with version_id"
}
```

**Response** (400 Bad Request - invalid pkl format):
```json
{
  "error": "Model file is not a valid joblib pickle",
  "error_code": "MODEL_001"
}
```

**Response** (403 Forbidden):
```json
{
  "error": "Only admins can upload models",
  "error_code": "AUTHZ_002"
}
```

---

### POST /admin/activate-model/{version_id}

**Description**: Activate a model version (marks as active; deactivates previous)

**Access**: ADMIN only

**Path Parameters**:
- `version_id` (UUID): Model version to activate

**Request**: Empty body (POST with no data)

**Example Request**:
```
POST /api/admin/activate-model/ver-123
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "message": "Model activated successfully",
  "new_active_version": "model_v1709200000_rf_v2",
  "previous_active_version": "model_v1709164234_anomaly_forest.pkl",
  "activated_at": "2026-03-11T10:35:00Z"
}
```

**Response** (409 Conflict - version already active):
```json
{
  "error": "Model version is already active",
  "error_code": "MODEL_002"
}
```

---

### GET /admin/models

**Description**: List all model versions with metrics

**Access**: ADMIN only

**Query Parameters**: None

**Example Request**:
```
GET /api/admin/models
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "data": [
    {
      "version_id": "ver-001",
      "version_name": "model_v1709164234_anomaly_forest.pkl",
      "uploaded_by": "admin_alice",
      "uploaded_at": "2026-03-05T08:00:00Z",
      "is_active": true,
      "metrics": {
        "precision": 0.9234,
        "recall": 0.9456,
        "f1_score": 0.9344,
        "training_date": "2026-03-05",
        "training_set_size": 600,
        "threshold": 0.914
      }
    },
    {
      "version_id": "ver-123",
      "version_name": "model_v1709200000_rf_v2",
      "uploaded_by": "admin_alice",
      "uploaded_at": "2026-03-11T10:30:00Z",
      "is_active": false,
      "metrics": {
        "precision": 0.9524,
        "recall": 1.0,
        "f1_score": 0.9756,
        "training_date": "2026-03-11"
      }
    }
  ],
  "total": 2
}
```

---

## Error Handling

**Standard Error Response Format**:
```json
{
  "error": "Human-readable error message",
  "error_code": "ERROR_NNN",
  "details": {
    "field": "Additional context (optional)"
  }
}
```

**Common HTTP Status Codes**:

| Code | Meaning | Scenario |
|------|---------|----------|
| 200 | OK | Successful GET/POST response |
| 201 | Created | Resource created (e.g., model upload) |
| 400 | Bad Request | Invalid query params, malformed JSON |
| 401 | Unauthorized | Missing/invalid JWT token |
| 403 | Forbidden | Authenticated but lack permission (role/category) |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | State conflict (e.g., model already active) |
| 422 | Unprocessable Entity | Validation failed (e.g., invalid category) |
| 500 | Internal Server Error | Unexpected server error (logs recorded) |

---

## Performance Targets

| Endpoint | p95 Latency | Notes |
|----------|-------------|-------|
| POST /auth/login | <200ms | JWT generation only; no DB read |
| GET /anomalies (50 items) | <500ms | Indexed query on (date, category, result) |
| GET /anomalies/{id} | <100ms | Direct UUID lookup + joins |
| GET /categories | <50ms | Cached in-memory (refreshed hourly) |
| GET /timeseries/{category} | <1000ms | Aggregated from 90+ days; can be pre-computed |
| POST /admin/retrain | <5000ms | File upload + model validation (joblib.load) |
| GET /admin/models | <100ms | Small result set; cached |

---

## Contract Status

✅ **Authentication (login, refresh) defined**
✅ **Anomaly list + filter (MVP feature)**
✅ **Anomaly detail (detailed explanations)**
✅ **Categories (reference data)**
✅ **Timeseries (charting data)**
✅ **Admin model management (versioning)**

**Ready for**: Frontend integration; Swagger/OpenAPI code generation; Backend implementation

