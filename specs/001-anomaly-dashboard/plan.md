# Implementation Plan: Anomaly Detection Dashboard

**Branch**: `001-anomaly-dashboard` | **Date**: 2026-03-11 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/001-anomaly-dashboard/spec.md`

## Summary

Build a full-stack anomaly detection dashboard with:
- **Backend**: Python 3.12 FastAPI service using hybrid anomaly detection (40% statistical method + 60% ML method) for real-time anomaly detection on daily financial transaction batches
- **Frontend**: React SPA with interactive time series charts, anomaly filtering, role-based views (Admin/Manager/Analyst)
- **Architecture**: Clean architecture (backend layers: domain → use case → adapters → framework) + JWT authentication + RBAC middleware
- **Data Pipeline**: Overnight (2 AM UTC) scheduled batch CSV import → hybrid anomaly scoring (statistical + ML fusion) → API exposure → dashboard display
- **Quality Gates**: TDD mandatory, 80%+ test coverage, pre-commit linting (ruff/black for Python, ESLint/Prettier for React), no production merge without CI/CD pass

## Technical Context

**Language/Version**: Python 3.12 (backend) + Node.js v24.13 (frontend)  
**Primary Dependencies**:
- Backend: FastAPI (REST API), scikit-learn (statistical + Isolation Forest methods), SQLAlchemy (ORM for audit logs), APScheduler (batch job scheduling), Pydantic (data validation), python-jose (JWT tokens), numpy/pandas (feature engineering for hybrid detection)
- Frontend: React 18+, Recharts or Plotly (time series charts), React Router (navigation), Axios (API client), TailwindCSS (styling)

**Storage**: SQLite (MVP prototype) or PostgreSQL (production-ready); audit logs normalized + indexed by (user_id, timestamp, model_version)  
**Testing**:
- Backend: pytest, pytest-cov (coverage), TestClient (FastAPI testing)
- Frontend: Vitest, React Testing Library, Mock Service Worker (MSW)

**Target Platform**: Linux server (backend), modern browsers Chrome/Firefox/Safari/Edge (frontend)  
**Project Type**: Full-stack web application (monorepo: backend/ + frontend/)  
**Performance Goals**:
- API response time: ≤500ms (list anomalies), ≤200ms (category list)
- Chart rendering: ≤2 seconds for 365+ data points
- Dashboard load: ≤3 seconds on 4G
- Filter update: ≤1 second (no page reload)

**Constraints**:
- <100ms interaction latency on UI (touch responsiveness)
- <500KB gzipped bundle size (initial load)
- 99% uptime during business hours
- 1-year audit log retention; daily batch window 2:00-3:00 AM UTC

**Scale/Scope**:
- ≤10,000 daily transactions (MVP)
- ~15 financial categories
- 3 user roles (Admin, Manager, Analyst)
- ~100-500 anomalies per day (based on trained model @ 95% precision)
- Supports 10+ concurrent users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Anomaly Detector Constitution v1.0.0** (Ratified 2026-03-11):

### I. Clean Architecture ✅
- **Requirement**: Backend domain → use case → adapters → framework layers; frontend components → hooks → services → API clients
- **Plan Compliance**: Phase 1 will define layered API structure (handlers → services → models → persistence layer); frontend will use container/presentational components with custom hooks for API calls
- **Status**: ALIGNED — No conflicts identified

### II. Quality-First Development ✅
- **Requirement**: TDD mandatory (write failing tests first), 80%+ coverage, pre-commit linting (ruff/black Python, ESLint/Prettier React)
- **Plan Compliance**: Task list will require unit + integration tests before feature completion; pre-commit hooks configured in Phase 1; CI/CD gates enforced (no merge on test failure or coverage drop)
- **Status**: ALIGNED — No conflicts identified

### III. User-Centric Excellence ✅
- **Requirement**: Accept criteria validation; intuitive UX; <100ms latency; comprehensive error messages
- **Plan Compliance**: All feature tasks include acceptance scenario testing; filter/chart interactions target <1s; API responses include meaningful error details (field-level validation messages)
- **Status**: ALIGNED — No conflicts identified

### IV. Performance & Observability ✅
- **Requirement**: Structured logging (correlation IDs, request tracing); DB query indexing; bundle <500KB; Core Web Vitals tracking
- **Plan Compliance**: FastAPI middleware will log correlation IDs; SQLite/PostgreSQL will index audit_logs(user_id, timestamp); Vite build config will monitor bundle size; Lighthouse CI will track Core Web Vitals
- **Status**: ALIGNED — No conflicts identified

### V. Dependency Management via UV ✅
- **Requirement**: UV for Python (lock files committed), npm + package-lock.json for JS; monthly security audits
- **Plan Compliance**: Backend uses UV exclusively; pyproject.toml + uv.lock committed; frontend uses npm with package-lock.json; security scanning (snyk for JS, bandit for Python) integrated into CI
- **Status**: ALIGNED — No conflicts identified

**Overall Constitution Check**: ✅ **ALL PRINCIPLES ALIGNED**  
No gate violations identified. Plan fully compliant with project constitution.

## Project Structure

### Documentation (this feature)

```text
specs/001-anomaly-dashboard/
├── spec.md                          # Feature specification (✅ DONE)
├── plan.md                          # This file (/speckit.plan output)
├── research.md                      # Phase 0 output - tech research
├── data-model.md                    # Phase 1 output - ER diagram, schema design
├── quickstart.md                    # Phase 1 output - dev environment setup
├── contracts/                       # Phase 1 output - API contracts folder
│   ├── api-endpoints.md             #   RESTful endpoints + request/response schemas
│   ├── auth-roles.md                #   Role definitions, permission matrix
│   └── data-schemas.md              #   Request/response JSON schemas (OpenAPI)
└── tasks.md                         # Phase 2 output - task list (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml                   # UV project config, dependencies
├── uv.lock                          # Locked dependency versions
├── .env.example                     # Environment variable template
├── src/
│   ├── main.py                      # FastAPI app initialization
│   ├── config.py                    # Settings (DB URL, batch time, model path, JWT secret)
│   ├── dependencies.py              # Shared dependencies (DB session, current user)
│   ├── models/                      # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── transaction.py           # Transaction entity
│   │   ├── anomaly_detection.py     # AnomalyDetectionResult entity
│   │   ├── audit_log.py             # AuditLog entity (1-year retention)
│   │   └── user.py                  # User entity (auth + roles)
│   ├── schemas/                     # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── anomaly.py               # AnomalyResponse schema
│   │   ├── transaction.py           # TransactionRequest schema
│   │   └── user.py                  # UserResponse, RoleEnum schemas
│   ├── services/                    # Business logic (use cases)
│   │   ├── __init__.py
│   │   ├── anomaly_detector.py      # Load model, run inference, generate explanations
│   │   ├── batch_processor.py       # CSV import, daily batch orchestration
│   │   ├── auth_service.py          # JWT token generation, role verification
│   │   └── audit_logger.py          # Log user actions + detections
│   ├── api/                         # API route handlers (adapters)
│   │   ├── __init__.py
│   │   ├── anomalies.py             # GET /api/anomalies, /api/anomalies/{id}
│   │   ├── categories.py            # GET /api/categories
│   │   ├── timeseries.py            # GET /api/timeseries/{category}
│   │   ├── admin.py                 # POST /api/admin/retrain (model upload)
│   │   └── auth.py                  # POST /api/auth/login, /api/auth/logout
│   ├── middleware/                  # Cross-cutting concerns
│   │   ├── __init__.py
│   │   ├── auth.py                  # JWT verification
│   │   ├── rbac.py                  # Role-based access control
│   │   └── logging.py               # Correlation ID, request tracing
│   ├── ml/                          # ML model interface
│   │   ├── __init__.py
│   │   └── anomaly_model.py         # Load .pkl, run inference, return scores
│   └── utils/                       # Utilities
│       ├── __init__.py
│       ├── explanations.py          # GenerateExplanation(scores, category, amount)
│       └── db_utils.py              # Archive audit logs (1-year policy)
├── tests/
│   ├── conftest.py                  # Pytest fixtures (DB, FastAPI TestClient)
│   ├── unit/
│   │   ├── test_anomaly_detector.py
│   │   ├── test_batch_processor.py
│   │   ├── test_auth_service.py
│   │   ├── test_explanations.py
│   │   └── test_audit_logger.py
│   ├── integration/
│   │   ├── test_api_anomalies.py    # Test GET /api/anomalies + filters
│   │   ├── test_api_auth.py         # Test auth endpoints
│   │   ├── test_batch_job.py        # Test daily batch import
│   │   └── test_rbac.py             # Test role-based endpoint access
│   └── contract/
│       └── test_api_contract.py     # Validate API response schemas
├── scripts/
│   ├── init_db.py                   # Create tables, seed initial data
│   └── train_model.py               # Placeholder (model is pre-trained; used for v1.1)
└── README.md                        # Backend setup + architecture

frontend/
├── package.json                     # npm project, dependencies
├── package-lock.json                # Locked npm versions
├── .env.example                     # API endpoint, auth config
├── index.html                       # HTML entry point
├── src/
│   ├── main.tsx                     # React + TypeScript entry
│   ├── App.tsx                      # Root component, routing
│   ├── vite-env.d.ts                # Vite type definitions
│   ├── components/
│   │   ├── Navbar.tsx               # Header + role-specific menu
│   │   ├── AnomalyList.tsx          # Table: Date, Category, Amount, Score
│   │   ├── AnomalyFilters.tsx       # Date range, category, severity, type filters
│   │   ├── AnomalyDetail.tsx        # Modal: Base Explanation, Cause, Advice
│   │   ├── Chart.tsx                # Recharts line chart + anomalies
│   │   ├── AdminPanel.tsx           # Model upload + version history (Admin only)
│   │   └── LoadingSpinner.tsx       # Shared loading state
│   ├── hooks/
│   │   ├── useAnomalies.ts          # Fetch anomalies, apply filters
│   │   ├── useCategories.ts         # Fetch category list
│   │   ├── useTimeSeries.ts         # Fetch chart data on-demand
│   │   ├── useAuth.ts               # Login, token refresh, role check
│   │   └── useFilters.ts            # Manage filter state (date, category, severity)
│   ├── services/
│   │   └── api.ts                   # Axios instance (base URL, auth header, error handling)
│   ├── pages/
│   │   ├── DashboardPage.tsx        # Main anomaly view (US1-4)
│   │   ├── LoginPage.tsx            # Auth form
│   │   └── AdminPage.tsx            # Model management (Admin role)
│   ├── styles/
│   │   └── index.css                # TailwindCSS
│   └── types/
│       └── index.ts                 # TypeScript interfaces (Anomaly, User, Filter)
├── tests/
│   ├── unit/
│   │   ├── components/
│   │   │   ├── AnomalyList.test.tsx
│   │   │   ├── AnomalyFilters.test.tsx
│   │   │   └── AdminPanel.test.tsx
│   │   └── hooks/
│   │       ├── useAnomalies.test.ts
│   │       ├── useAuth.test.ts
│   │       └── useFilters.test.ts
│   ├── integration/
│   │   ├── dashboard-flow.test.tsx  # E2E: login → view anomalies → filter → details
│   │   └── admin-flow.test.tsx      # E2E: admin login → upload model → verify
│   └── setup.ts                     # Vitest + MSW mock API setup
├── vite.config.ts                   # Vite configuration + bundle size monitoring
└── README.md                        # Frontend setup, component architecture

root/
├── docker-compose.yml               # PostgreSQL + backend + frontend (optional)
├── .gitignore
├── README.md                        # Project overview
└── .github/
    ├── workflows/
    │   ├── test-backend.yml         # pytest + coverage
    │   ├── test-frontend.yml        # vitest, ESLint, Prettier
    │   ├── lint-backend.yml         # ruff, black, mypy
    │   ├── lint-frontend.yml        # ESLint, Prettier
    │   └── security.yml             # bandit (Python), snyk (JS)
    └── PULL_REQUEST_TEMPLATE.md     # Verify constitution principles + 80% coverage
```

**Structure Decision**: Monorepo with separate backend/frontend folders enables independent scaling and deployment while maintaining shared constitution and CI/CD standards. Backend uses layered architecture (FastAPI handlers → services → data models → SQLAlchemy ORM); frontend uses component hierarchy with custom hooks for data fetching.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**Status**: ✅ No violations. All constitution principles aligned with plan design.

---

## Phase 0: Research & Design Research

**OUTPUT**: `research.md` with all unknowns resolved

### Research Tasks (Auto-dispatch to subagent)

**Task 1: FastAPI + JWT Authentication Architecture**
- Research modern FastAPI patterns for role-based middleware
- Find best practices for JWT token refresh, logout handling, RBAC enforcement at endpoint level
- Decision: Which RBAC library (Depends vs. custom)?
- Decision: SQLite vs. PostgreSQL for audit logs in MVP?

**Task 2: React Time Series Charting & Filtering**
- Evaluate Recharts vs. Plotly vs. Chart.js for interactive charts with large datasets
- Research React patterns for multi-filter state management (useCallback, useMemo)
- Best practices for on-demand data loading (infinite scroll vs. pagination)

**Task 3: Daily Batch Job Scheduling in Python**
- Compare APScheduler vs. Celery vs. schedule library for simple daily batch
- Decision: Where to run scheduler (main FastAPI process vs. separate worker)?
- Decision: CSV upload mechanism (file API endpoint vs. scheduled S3 pull)?

**Task 4: Audit Logging & 1-Year Retention Policy**
- Design audit log schema (user_id, action, timestamp, affected_record_id, model_version)
- Research archival strategies (cold storage after 1 year, soft delete vs. hard delete at 2 years)
- Decision: Should audit logs be separate from transactions table or normalized?

**Task 5: Hybrid Statistical + ML Anomaly Detection Model**
- Document the anomaly.ipynb model interface: both statistical method (rolling MAD + modified Z-score) and ML method (Isolation Forest on windowed features)
- Design score fusion architecture: 40% statistical + 60% ML weighted combination
- Create cause classification logic based on which method's score dominates
- Model versioning strategy: pickle + ModelVersion table for audit/rollback
- Decision: How to normalize and fuse scores across different scales?
- Decision: Model reload without downtime during re-training or version switch?

---

## Phase 1: Design & Contracts

**PREREQUISITES**: research.md complete

### Deliverable 1: Data Model (data-model.md)

**Entities & Relationships**:

1. **User** (Authentication & Authorization)
   - user_id: UUID (primary key)
   - username: string (unique)
   - password_hash: string
   - role: enum(Admin | Manager | Analyst)
   - created_at: timestamp
   - last_login: timestamp

2. **Transaction**
   - transaction_id: UUID (PK)
   - date: date
   - category: string (foreign key: Category table)
   - amount: float
   - source: string (optional)
   - created_at: timestamp
   - Index: (date, category) for batch queries

3. **AnomalyDetectionResult**
   - detection_id: UUID (PK)
   - transaction_id: UUID (FK)
   - stats_score: float (0-1, from rolling MAD + modified Z-score)
   - ml_score: float (0-1, from Isolation Forest on engineered features)
   - combined_score: float (0-1, fused as 0.4×stats + 0.6×ml)
   - result: enum(Normal | Anomaly)
   - base_explanation: string
   - cause: enum(statistical_spike | ml_pattern_anomaly | hybrid_confirmed | system_level_anomaly | normal)
   - advice: string
   - model_version: string (tracks which model version produced this detection)
   - created_at: timestamp
   - Index: (transaction_id, result, created_at) for filtering

4. **AuditLog** (Compliance & 1-Year Retention)
   - log_id: UUID (PK)
   - user_id: UUID (FK)
   - action: string (e.g., "LOGIN", "DOWNLOAD_EXPORT", "RETRAIN_MODEL")
   - resource_type: string (e.g., "Anomaly", "User", "Model")
   - resource_id: UUID (optional)
   - details: JSON (context-specific metadata)
   - timestamp: timestamp
   - created_at: timestamp
   - archived_at: timestamp (NULL until 1 year, then set for soft delete; hard delete at 2 years)
   - Index: (user_id, timestamp) for audit queries, (archived_at) for cleanup jobs

5. **ModelVersion** (Track retraining & inference versions)
   - version_id: UUID (PK)
   - version_name: string (e.g., "v1_2025_03_11_isolation_forest")
   - uploaded_by: UUID (FK to User, must be Admin)
   - uploaded_at: timestamp
   - is_active: boolean (only one active at a time)
   - model_path: string (file path or S3 key)
   - metrics: JSON (precision, recall, F1 from training/test)
   - created_at: timestamp

6. **Category**
   - category_id: int (PK)
   - name: string (unique)
   - description: string (optional)

**Validation Rules**:
- combined_score must be between 0 and 1
- result enum values only: Normal or Anomaly
- cause enum values only: 5 types + normal
- AuditLog.archived_at set 365 days after created_at (cron job)
- Only one ModelVersion.is_active = true at a time (constraint or application logic)

**State Transitions**:
- Transaction → AnomalyDetectionResult (one-to-one; after batch import + inference)
- User action → AuditLog entry (after every login, export, model retrain)
- ModelVersion → active (manual via Admin UI; old versions archived)

### Deliverable 2: API Contracts (contracts/ folder)

**File 1: contracts/api-endpoints.md**

```
GET /api/anomalies
  Query: date_from, date_to, category[], severity[], anomaly_type[], page, per_page
  Response: {
    data: [ { detection_id, transaction_id, date, category, amount, combined_score, cause, result } ],
    meta: { total, page, per_page }
  }
  Auth: Any role (Analyst sees own categories, Manager sees all)
  Tests: filter by date, category, severity; pagination; RBAC enforcement

GET /api/anomalies/{detection_id}
  Response: { detection_id, date, category, amount, stats_score, ml_score, combined_score, base_explanation, cause, advice }
  Auth: Any role (Analyst can only view assigned categories)
  Tests: Correct explanation format; role-based access

GET /api/categories
  Response: [ { category_id, name, description } ]
  Auth: Any role
  Tests: Returns all categories; frontend can populate dropdown

GET /api/timeseries/{category}
  Query: date_from, date_to
  Response: [ { date, amount, is_anomaly, anomaly_score } ]
  Auth: Any role
  Tests: Correct data for chart rendering; handles missing data

POST /api/auth/login
  Request: { username, password }
  Response: { access_token, user: { user_id, username, role } }
  Tests: Valid creds return token; invalid return 401; token can decode role

POST /api/admin/retrain
  Request: multipart file (model.pkl)
  Response: { version_id, version_name, metrics, active }
  Auth: Admin only
  Tests: RBAC enforced; file upload sanitized; model versioning logged

GET /api/admin/models
  Response: [ { version_id, version_name, uploaded_at, is_active, metrics } ]
  Auth: Admin only
  Tests: List all model versions with timestamps
```

**File 2: contracts/auth-roles.md**

```
Role Definitions:
- ADMIN: Can upload/retrain models, create/delete users, modify system parameters (thresholds, batch time)
- MANAGER: Can view all category anomalies, approve/dismiss alerts, access audit logs, export data
- ANALYST: Can view assigned category anomalies, create investigation notes, view explanations

RBAC Matrix:
| Resource | GET | POST | PUT | DELETE | ADMIN | MANAGER | ANALYST |
|----------|-----|------|-----|--------|-------|---------|---------|
| /anomalies | Y | N | N | N | All | All | Own Cats |
| /anomalies/{id} | Y | N | N | N | All | All | Own Cats |
| /categories | Y | N | N | N | All | All | All |
| /timeseries | Y | N | N | N | All | All | All |
| /admin/retrain | N | Y | N | N | Y | N | N |
| /admin/models | Y | N | N | N | Y | N | N |
| /admin/users | Y | Y | Y | Y | Y | N | N |
| /audit/logs | Y | N | N | N | Y | Y | N |
```

**File 3: contracts/data-schemas.md** (OpenAPI/JSON Schema)

```json
AnomalyResponse:
{
  "detection_id": "uuid",
  "date": "2026-03-11",
  "category": "Average Fast Food format Check",
  "amount": 15.50,
  "combined_score": 0.82,
  "cause": "sudden_spike",
  "result": "Anomaly",
  "base_explanation": "ML Pattern anomaly... Statistical outlier..."
}

FilterParams:
{
  "date_from": "2026-01-01",
  "date_to": "2026-03-11",
  "categories": ["Average Fast Food format Check", "Average check in Restaurant format"],
  "severity": ["High"],  // Low | Medium | High (severity ranges: Low: 0-0.33, Med: 0.33-0.66, High: 0.66-1.0)
  "anomaly_type": ["sudden_spike", "sharp_change"],  // from cause enum
  "page": 1,
  "per_page": 50
}

TimeSeriesPoint:
{
  "date": "2026-01-01",
  "amount": 150.25,
  "is_anomaly": false,
  "anomaly_score": 0.12
}
```

### Deliverable 3: Agent Context Update

Run `update-agent-context.ps1` to inject this plan into agent system prompts.

**Update Copilot Context**:
- Technology choices: Python 3.12 FastAPI, React 18, SQLite/PostgreSQL, APScheduler
- Architecture: Monorepo backend/frontend; layered backend; JWT + RBAC
- Key entities: User (3 roles), Transaction, AnomalyDetectionResult, AuditLog (1-yr), ModelVersion
- API pattern: RESTful; role-based endpoint filtering; pagination
- Data pipeline: Nightly CSV batch → inference loop → DB write → API exposure
- Quality gates: pytest + 80% coverage (backend), vitest (frontend), pre-commit linting, no merge on test fail

### Deliverable 4: Quickstart Guide (quickstart.md)

**Backend Setup**:
```bash
cd backend
uv venv
uv sync
cp .env.example .env  # Set DB_URL, JWT_SECRET, BATCH_TIME=02:00
python scripts/init_db.py
python src/main.py
# Server runs on http://localhost:8000; docs at /docs
```

**Frontend Setup**:
```bash
cd frontend
npm install
cp .env.example .env  # Set VITE_API_URL=http://localhost:8000
npm run dev
# App runs on http://localhost:5173
```

---

## Gate Evaluation (Post-Phase-1)

*GATE: Re-evaluate Constitution Check after Phase 1 design*

**Constitution Principles Status**:

| Principle | Phase 0 Assessment | Phase 1 Assessment | Conflicts? |
|-----------|-------------------|-------------------|-----------|
| I. Clean Architecture | Research confirmed FastAPI layering patterns | Detailed layer definitions in data-model.md; component/hook patterns for frontend | ✅ None |
| II. Quality-First Development | Research confirmed pytest + coverage tools | Task list will enforce unit + integration tests; pre-commit hooks defined | ✅ None |
| III. User-Centric Excellence | Confirmed <100ms interaction targets are achievable with React + Recharts | Filter/chart UX with pagination + lazy loading achieves sub-1s updates | ✅ None |
| IV. Performance & Observability | Research confirmed FastAPI middleware + SQLite indexing patterns | Middleware layer defined in project structure; bundle size monitoring in Vite config | ✅ None |
| V. Dependency Management via UV | Research confirmed UV + uv.lock best practices | Backend uses UV explicitly; frontend uses npm; monthly security audits in CI | ✅ None |

**Overall**: ✅ **POST-PHASE-1 CONSTITUTION CHECK PASSES**  
All principles remain aligned after detailed design. No new conflicts introduced.

---

### PHASE 0 & 1 Completion Summary

**Generated Artifacts**:
- ✅ `research.md` — Tech stack research (FastAPI patterns, charting libraries, batch scheduling, audit logging, ML integration)
- ✅ `data-model.md` — 6 entities, relationships, validation rules, state transitions
- ✅ `quickstart.md` — Backend + frontend setup instructions
- ✅ `contracts/` folder with 3 files: API endpoints, role definitions, data schemas
- ✅ Agent context updated with tech choices and architecture patterns
- ✅ Post-design Constitution Check: PASSES

**Next Phase**: `/speckit.tasks` will generate dependency-ordered task list from this plan.

