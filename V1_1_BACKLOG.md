# v1.1 Feature Backlog

**Date**: March 12, 2026  
**Purpose**: Document features deferred from MVP v1.0 for v1.1 release  
**Estimated Timeline**: 4-6 weeks post-MVP launch

---

## Overview

This document tracks all planned features for **v1.1** release, deferred from MVP v1.0 to maintain production readiness and fast deployment.

| Feature | Status | Spec Phase | Task Count | Effort | Priority |
|---------|--------|-----------|-----------|--------|----------|
| **Phase 7: Batch Processing** | DEFERRED | P1 | 14 tasks | 3-4 weeks | HIGH |
| **Phase 8: Admin Model Management** | DEFERRED | P1 | 10 tasks | 2-3 weeks | HIGH |
| **User Story 5: System Overview** | DEFERRED | P2 | ~8 tasks | 1-2 weeks | MEDIUM |
| **User Story 6: Export/PDF Reports** | DEFERRED | P3 | ~8 tasks | 1-2 weeks | LOW |
| **Phase 10 Polish (Remaining)** | PARTIAL | P/O | ~5 tasks | 1 week | MEDIUM |

---

## Phase 7: Batch Processing Pipeline

**Goal**: Enable daily automated CSV import and anomaly detection via scheduled batch job

### Context
- **v1.0 Status**: Inference-only (API-driven anomaly detection works; no scheduled batching)
- **v1.0 Limitation**: Users must call `/api/anomalies/detect` endpoint manually or via external scheduler
- **v1.1 Benefit**: Automatic daily 2 AM UTC batch import + detection without manual intervention

### Requirements

**FR-002** (Batch Import):
- Accept daily CSV file (Date, Categories, Amount) via upload or SFTP
- Validate CSV: required fields, data types, ranges
- Duplicate detection by (date, category, amount)
- Process validation errors: skip invalid rows, log errors, continue with valid rows

**FR-015** (Scheduling):
- APScheduler job triggers at 2 AM UTC daily
- Batch processes all new transactions + runs anomaly detection
- Failure recovery: auto-retry 2 times with exponential backoff
- Admin alert on final failure with error details

**FR-015** (Recovery):
- Partial success: process valid rows, skip invalid
- Rollback on critical errors (DB connection, ML model load)
- Manual retry endpoint for admins

### Implementation Tasks (Phase 7: T082-T095)

| Task | Name | Description | Effort | Notes |
|------|------|-------------|--------|-------|
| T082 | CSV Schema Validation | Create utility to validate CSV structure, fields, data types | 1 day | Reusable across all batch imports |
| T083 | Batch Job Handler | Main batch orchestrator (read CSV → validate → process) | 2 days | Coordinate sub-tasks T084-T087 |
| T084 | Transaction Ingestion | Parse CSV, insert into Transaction table with duplicate detection | 1 day | Filter out duplicates before processing |
| T085 | Anomaly Detection | Run hybrid scoring (stats + ML) on ingested transactions | 1 day | Reuse existing anomaly_detector service |
| T086 | Explanation Generation | Generate cause + advice explanations for each detected anomaly | 1 day | Template-based per cause type |
| T087 | Result Persistence | Insert AnomalyDetectionResults into database with full metadata | 1 day | Include model_version, timestamp, scores |
| T088 | Failure Recovery | Auto-retry logic with exponential backoff (T1=2s, T2=10s) | 1 day | Max 2 retries per batch |
| T089 | Admin Alerts | Send email/dashboard notification on final batch failure | 1 day | Include error summary |
| T090 | APScheduler Setup | Configure daily 2 AM UTC trigger in main.py | 1 day | Use APScheduler BackgroundScheduler |
| T091 | Manual Trigger Endpoint | POST /api/admin/batch/trigger (admin-only) | 1 day | Testing + on-demand runs |
| T092 | Batch Status Endpoint | GET /api/admin/batch/status returning last run + metrics | 1 day | Include processed count, error count, duration |
| T093 | Unit Tests | pytest for CSV validation, transaction ingestion, anomaly detection | 2 days | Mocked dependencies |
| T094 | Integration Tests | End-to-end test: CSV → validation → detection → DB | 2 days | Real DB setup/teardown |
| T095 | Failure Recovery Tests | Test retry logic, admin alerts, rollback scenarios | 1 day | Edge cases (network timeout, model load failure) |

**Total Effort**: 3-4 weeks (1 developer)

### API Changes

```python
# New endpoint: Manual batch trigger
POST /api/admin/batch/trigger
# Response:
{
  "batch_id": "batch_20260401_020000",
  "status": "processing",
  "started_at": "2026-04-01T02:00:00Z"
}

# New endpoint: Batch status
GET /api/admin/batch/status
# Response:
{
  "last_batch": {
    "batch_id": "batch_20260401_020000",
    "status": "completed",  # completed, failed, processing
    "started_at": "2026-04-01T02:00:00Z",
    "completed_at": "2026-04-01T02:12:34Z",
    "transactions_processed": 15234,
    "transactions_skipped": 12,  # duplicates
    "invalid_rows": 3,
    "anomalies_detected": 142,
    "error_message": null
  },
  "next_scheduled": "2026-04-02T02:00:00Z"
}

# New endpoint: Batch history
GET /api/admin/batch/history?limit=10
# Response: List of last 10 batch runs with summary stats
```

### Database Changes

```python
# New table: BatchRun
class BatchRun(Base):
    __tablename__ = "batch_runs"
    
    batch_id = Column(String, primary_key=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String)  # processing, completed, failed
    transactions_processed = Column(Integer)
    transactions_skipped = Column(Integer)
    invalid_rows = Column(Integer)
    anomalies_detected = Column(Integer)
    error_message = Column(String, nullable=True)
```

### Testing

```bash
# Unit tests
pytest tests/unit/test_batch_processor.py -v

# Integration tests
pytest tests/integration/test_batch_pipeline.py -v

# Load test (1000s of transactions)
pytest tests/load/test_batch_scale.py -v

# Test retry logic
pytest tests/integration/test_batch_recovery.py -v
```

---

## Phase 8: Admin Model Management

**Goal**: Enable admins to upload, version, and activate new ML models without code changes

### Context
- **v1.0 Status**: Uses pre-trained model loaded on startup (inference-only)
- **v1.0 Limitation**: Retraining requires code change + redeploy
- **v1.1 Benefit**: Admins can upload new models via UI, activate with one click

### Requirements

**FR-001** (Model Versioning):
- Upload .pkl file containing trained model
- Assign version name + notes
- Store version history (upload date, model metrics, upload by)
- Only one model active at a time

**Admin UI** (Model Management):
- Upload form (drag-drop .pkl file)
- Version history table (version, upload date, metrics, status)
- Activate button to switch active model
- Activation scheduled for next batch job (not retroactive)

### Implementation Tasks (Phase 8: T096-T105)

| Task | Name | Description | Effort |
|------|------|-------------|--------|
| T096 | Model File Validation | Validate .pkl files (magic bytes, not executable) | 1 day |
| T097 | ModelVersion Service | Create + list + activate versions in database | 2 days |
| T098 | Activation Logic | Ensure only one model active; switch safe | 1 day |
| T099 | POST /api/admin/models/upload | Model upload endpoint with auth | 1 day |
| T100 | GET /api/admin/models | List version history endpoint | 1 day |
| T101 | POST /api/admin/models/{id}/activate | Activate model endpoint | 1 day |
| T102 | Admin Model UI | React component: upload form + version table | 2 days |
| T103 | Unit Tests | pytest for model versioning + activation | 1 day |
| T104 | Integration Tests | Test upload, list, activate endpoints | 1 day |
| T105 | Component Tests | React component tests (upload, version list) | 1 day |

**Total Effort**: 2-3 weeks (1 developer)

### API

```python
# Upload model
POST /api/admin/models/upload
# Multipart form data:
# - file: <model.pkl>
# - version: "2026_04_pretrained_v2"
# - notes: "Retrained on 2026-03 data"
# Response:
{
  "model_id": "model_20260410_152030",
  "version": "2026_04_pretrained_v2",
  "uploaded_by": "admin@example.com",
  "uploaded_at": "2026-04-10T15:20:30Z",
  "is_active": false,
  "notes": "Retrained on 2026-03 data"
}

# List versions
GET /api/admin/models
# Response:
{
  "versions": [
    {
      "model_id": "model_initial",
      "version": "initial_baseline",
      "uploaded_at": "2026-03-01T00:00:00Z",
      "uploaded_by": "data_team@example.com",
      "is_active": true,
      "notes": "Pre-trained baseline model"
    },
    {
      "model_id": "model_20260410_152030",
      "version": "2026_04_pretrained_v2",
      "uploaded_at": "2026-04-10T15:20:30Z",
      "uploaded_by": "admin@example.com",
      "is_active": false,
      "notes": "Retrained on 2026-03 data"
    }
  ]
}

# Activate model
POST /api/admin/models/{model_id}/activate
# Response:
{
  "activated_model_id": "model_20260410_152030",
  "previous_model_id": "model_initial",
  "activation_timestamp": "2026-04-10T15:25:00Z",
  "effective_from": "next batch (2026-04-11T02:00:00Z)"
}
```

### Database

```python
class ModelVersion(Base):
    __tablename__ = "model_versions"
    
    model_id = Column(String, primary_key=True)
    version = Column(String, unique=True)
    file_path = Column(String)  # S3 or local path
    uploaded_at = Column(DateTime)
    uploaded_by = Column(String)  # user_id or email
    is_active = Column(Boolean, default=False)
    metrics = Column(JSON, nullable=True)  # {'precision': 0.95, 'recall': 0.92, ...}
    notes = Column(String, nullable=True)
```

---

## User Story 5: System-Level Monitoring

**Goal**: Aggregate anomalies across all categories to show system health + trends

### Context
- **v1.0 Status**: Category-level analysis only
- **v1.0 Limitation**: Cannot see "system-wide anomaly trend"
- **v1.1 Benefit**: Risk managers can monitor system anomalies + total transaction volume

### Requirements

**System Overview Dashboard**:
- Total transactions per day (last 90 days, time series chart)
- Total anomalies per day (highlighted on same chart)
- System anomaly rate (anomalies / total transactions)
- Top anomalous categories this week
- System health score (0-100 based on anomaly rate)

**API**:
- GET /api/system-overview (returns aggregates)
- GET /api/system-overview/trends (time series data)

### Implementation Tasks

| Task | Name | Effort |
|------|------|--------|
| ~T106 | Aggregation Service | Sum anomalies + transactions by date | 1 day |
| ~T107 | System Overview Endpoint | GET /api/system-overview | 1 day |
| ~T108 | Trends Endpoint | GET /api/system-overview/trends | 1 day |
| ~T109 | System Health Calculation | Anomaly rate → health score (0-100) | 1 day |
| ~T110 | System Overview UI | React component: charts + metrics | 2 days |
| ~T111 | Integration Tests | Test aggregation endpoints | 1 day |
| ~T112 | Component Tests | Test system overview UI | 1 day |

**Total Effort**: 1-2 weeks

---

## User Story 6: Export & Report Generation

**Goal**: Enable users to export anomalies and generate PDF reports

### Context
- **v1.0 Status**: Dashboard view only
- **v1.0 Limitation**: Cannot export for email/Slack/report sharing
- **v1.1 Benefit**: Users can share findings with non-technical stakeholders

### Requirements

**CSV Export**:
- Export anomaly list (all visible columns + explanations)
- Filtered by current view (date, category, severity)
- Downloaded as `anomalies_YYYYMMDD.csv`

**PDF Report**:
- Title page (generated date, user, filters)
- Summary: total anomalies, by severity, by category
- Time series chart (anomalies over selected period)
- Top anomalies table (top 20 by score)
- Category breakdown
- Appendix: detailed anomaly list

### Implementation Tasks

| Task | Name | Effort |
|------|------|--------|
| ~T113 | CSV Export Service | Generate + stream CSV from anomaly list | 1 day |
| ~T114 | CSV Button UI | React button: "Export as CSV" | 1 day |
| ~T115 | PDF Generation Service | Puppeteer or reportlab for PDF | 2 days |
| ~T116 | PDF Button UI | React button: "Generate PDF Report" | 1 day |
| ~T117 | Email PDF | Optional: email report to user | 1 day |
| ~T118 | Integration Tests | Test CSV + PDF endpoints | 1 day |
| ~T119 | Component Tests | Test export buttons | 1 day |

**Total Effort**: 1-2 weeks

---

## Phase 10 Polish (Remaining)

### Structured Logging with Correlation IDs

**Goal**: Every request tagged with unique ID for end-to-end tracing

**Implementation**:
```python
# Middleware adds correlation_id to all requests
from uuid import uuid4
from fastapi import Request

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
    request.state.correlation_id = correlation_id
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response

# All logs include correlation_id
logger.info(f"Anomaly detected", extra={"correlation_id": request.state.correlation_id})
```

**Effort**: 1-2 days

### Production CORS & Security Configuration

**Goal**: Harden security headers for production deployment

**Implementation**:
```python
from fastapi.middleware.cors import CORSMiddleware

# Strict CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,
)

# Security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

**Effort**: 1 day

### Database Query Optimization

**Goal**: Add missing indexes + optimize slow queries

**Implementation**:
```python
# Create indexes on frequently filtered columns
# In migration or direct SQL:
CREATE INDEX idx_audit_logs_user_timestamp ON audit_logs(user_id, timestamp DESC);
CREATE INDEX idx_anomaly_results_created ON anomaly_detection_results(created_at DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);

# In SQLAlchemy model:
class AnomalyDetectionResult(Base):
    __tablename__ = "anomaly_detection_results"
    __table_args__ = (
        Index('idx_anomaly_created_at', 'created_at', mysql_length={'created_at': 32}),
    )
```

**Effort**: 1-2 days

---

## Release Timeline

### Week 1: Planning & Design
- [ ] Finalize Phase 7 task breakdown
- [ ] Finalize Phase 8 task breakdown
- [ ] Design API contracts for new endpoints
- [ ] Estimate resources + assign developers

### Week 2-3: Phase 7 Implementation
- [ ] T082-T087: CSV validation + batch processing
- [ ] T088-T092: Failure recovery + scheduling
- [ ] T093-T095: Testing

### Week 4-5: Phase 8 Implementation
- [ ] T096-T101: Model versioning + API
- [ ] T102-T105: Admin UI + tests

### Week 6: US5/US6 + Polish
- [ ] System Overview (1 week)
- [ ] Export/PDF (1 week)
- [ ] Structured Logging + Security Headers (polish)

### Week 7: Testing + Staging
- [ ] Full integration test suite
- [ ] Staging environment deployment
- [ ] UAT (User Acceptance Testing)
- [ ] Performance testing

### Week 8: Release
- [ ] Production deployment
- [ ] Monitoring + alerting
- [ ] User documentation
- [ ] Training materials

---

## Success Criteria

### Phase 7 (Batch)
- [x] Daily batch job runs at 2 AM UTC automatically
- [x] All new transactions processed without manual intervention
- [x] Failure recovery: admin notified on retry failure
- [x] Partial success: invalid rows skipped, valid rows processed
- [x] Batch status visible in admin panel

### Phase 8 (Admin)
- [x] Admins can upload .pkl models via UI
- [x] Version history displayed with metrics
- [x] Model activation scheduled for next batch
- [x] Only one model active at a time

### US5 (System Overview)
- [x] System overview dashboard accessible to Managers/Admins
- [x] Shows total anomalies + transactions (time series)
- [x] System health score calculated
- [x] Top anomalous categories listed

### US6 (Export)
- [x] CSV export works from anomaly list
- [x] PDF report includes charts + summary
- [x] Exports respect current filters
- [x] File downloads work on all browsers

---

## Related Documentation

- **v1.0 Specification**: [specs/001-anomaly-dashboard/spec.md](specs/001-anomaly-dashboard/spec.md)
- **Original Tasks**: [specs/001-anomaly-dashboard/tasks.md](specs/001-anomaly-dashboard/tasks.md)
- **Phase Mapping**: [PHASE_MAPPING.md](PHASE_MAPPING.md)
- **Deployment Readiness**: [DEPLOYMENT_READINESS.md](DEPLOYMENT_READINESS.md)

---

**Status**: PLANNED FOR v1.1  
**Last Updated**: March 12, 2026  
**Next Review**: Post-v1.0 launch (check market feedback before committing v1.1 timeline)
