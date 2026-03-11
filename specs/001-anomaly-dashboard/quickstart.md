# Quickstart Guide: Development Environment Setup

**Feature**: Anomaly Detection Dashboard  
**Version**: 1.0.0 MVP  
**Date**: 2026-03-11

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Backend Setup](#backend-setup)
3. [Frontend Setup](#frontend-setup)
4. [Database Initialization](#database-initialization)
5. [Running the Application](#running-the-application)
6. [API Documentation](#api-documentation)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **OS**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 20.04+)
- **RAM**: 8GB minimum (16GB recommended)
- **Disk**: 5GB free space

### Required Software

- **Python 3.12**: [Download](https://www.python.org/downloads/)
- **Node.js v24.13**: [Download](https://nodejs.org/)
- **Git**: [Download](https://git-scm.com/)
- **SQLite 3**: Pre-installed on macOS/Linux; Windows users get it with Python or [Download](https://www.sqlite.org/download.html)

### Installation Verification

```bash
# Verify Python
python --version
# Output: Python 3.12.x

# Verify Node.js
node --version
# Output: v24.13.x

npm --version
# Output: 10.x.x

# Verify Git
git --version
# Output: git version 2.x.x
```

---

## Backend Setup

### Step 1: Install UV Package Manager

UV is the package manager for this project (per Constitution).

**Windows (PowerShell)**:
```powershell
irm https://astral.sh/install.ps1 | iex
```

**macOS / Linux (Bash)**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Verify Installation**:
```bash
uv --version
# Output: uv X.X.X
```

### Step 2: Clone & Navigate to Repository

```bash
# Clone the repository (if not already cloned)
git clone <repository-url>
cd anomaly-detector

# Create and activate Python virtual environment
uv venv
# Windows: .\.venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Synchronize dependencies from pyproject.toml
uv sync

# Verify installation
uv pip list
```

**Key Backend Dependencies**:
- FastAPI: REST API framework
- Pydantic: Data validation
- SQLAlchemy: ORM for database
- scikit-learn: ML algorithms (Isolation Forest)
- joblib: Model serialization
- python-jose: JWT authentication
- APScheduler: Batch job scheduling
- Alembic: Database migrations

### Step 4: Configure Environment Variables

Create `.env` file in `backend/` directory:

```bash
# database
DATABASE_URL=sqlite:///./anomaly.db
SQLALCHEMY_ECHO=True  # Enable SQL query logging (development only)

# authentication
SECRET_KEY=your-super-secret-key-change-in-production-use-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# application
DEBUG=True
LOG_LEVEL=INFO
API_TITLE=Anomaly Detection Dashboard
API_VERSION=1.0.0

# batch processing
BATCH_SCHEDULE_HOUR=2
BATCH_SCHEDULE_MINUTE=0
CSV_UPLOAD_DIR=./data/uploads
MODEL_DIR=./models

# CORS (development)
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

**Important**: Change `SECRET_KEY` in production
```bash
# Generate secure key
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 5: Initialize Database

```bash
cd backend

# Create database schema (SQLAlchemy will auto-create tables)
python -c "from src.database import engine, Base; Base.metadata.create_all(bind=engine)"

# Seed initial categories
python scripts/seed_categories.py

# Verify database
ls -la anomaly.db
```

### Step 6: Train/Load ML Model

The model is pre-trained (from `anomaly.ipynb`). Place the model file:

```bash
# Create model directory
mkdir -p models

# Option A: Copy pre-trained model from notebook
cp /path/to/trained/model.pkl models/model_v_initial.pkl

# Option B: Re-train from notebook (advanced)
python scripts/train_model.py --data financial_data.csv --output models/model_v_initial.pkl

# Create initial ModelVersion record
python scripts/initialize_model.py --model-path models/model_v_initial.pkl --version-name model_v_initial
```

### Step 7: Start Backend Server

```bash
# From backend/ directory
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Output:
# Uvicorn running on http://0.0.0.0:8000
# API docs available at http://localhost:8000/docs
```

**Flags Explained**:
- `--reload`: Auto-restart on code changes (development only)
- `--host 0.0.0.0`: Listen on all network interfaces
- `--port 8000`: Serve on port 8000

---

## Frontend Setup

### Step 1: Navigate to Frontend Directory

```bash
cd frontend
```

### Step 2: Install Dependencies

```bash
# Install Node.js dependencies
npm install

# Verify installation
npm list
```

**Key Frontend Dependencies**:
- React 18+: UI framework
- React Router: Navigation
- Recharts: Time series charts
- React Hook Form: Multi-filter form state
- Axios: HTTP client
- TailwindCSS: Styling
- Vite: Build tool
- Vitest + React Testing Library: Testing

### Step 3: Configure Environment Variables

Create `.env.local` file in `frontend/` directory:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api
VITE_API_TIMEOUT=30000

# Application
VITE_APP_NAME=Anomaly Detection Dashboard
VITE_APP_VERSION=1.0.0

# Feature Flags
VITE_ENABLE_DEBUG_MODE=true
VITE_ENABLE_PERFORMANCE_MONITORING=true
```

**Note**: Variables must be prefixed with `VITE_` to be accessible in browser

### Step 4: Start Development Server

```bash
# From frontend/ directory
npm run dev

# Output:
# VITE v<version> ready in <time> ms
# ➜  Local:   http://localhost:5173/
```

### Step 5: Access Dashboard

Open in browser: [http://localhost:5173](http://localhost:5173)

---

## Database Initialization

### Create Database from Scratch

```bash
cd backend

# Option 1: Automatic (SQLAlchemy ORM)
python -c "
from src.database import engine, Base
Base.metadata.create_all(bind=engine)
print('Database tables created')
"

# Option 2: Manual SQL (if using PostgreSQL in production)
psql -U postgres -d anomaly_db < schemas/schema.sql
```

### Seed Initial Data

```bash
# Load financial transaction categories (one-time)
python scripts/seed_categories.py

# Import sample transactions from CSV (optional for testing)
python scripts/import_csv.py --file /path/to/financial_data.csv
```

### Verify Database

```bash
# Check SQLite database
sqlite3 anomaly.db ".tables"
# Output: anomaly_detection_result  audit_log  category  model_version  transaction  user

sqlite3 anomaly.db "SELECT COUNT(*) FROM category;"
# Output: 6 (or number of categories seeded)
```

---

## Running the Application

### Full Setup (All Services)

```bash
# Terminal 1: Backend
cd backend
uv venv && source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
uv sync
cp .env.example .env  # Create .env with values
python scripts/seed_categories.py  # One-time
uvicorn src.main:app --reload

# Terminal 2: Frontend
cd frontend
npm install
cp .env.example .env.local  # Create .env.local
npm run dev

# Terminal 3: (Optional) Database monitoring
sqlite3 anomaly.db "SELECT COUNT(*) FROM transaction; SELECT COUNT(*) FROM anomaly_detection_result;"
```

### Verify All Services Running

**Backend Health Check**:
```bash
curl -X GET "http://localhost:8000/api/health"
# Expected: {"status": "ok"}
```

**Frontend Access**:
- Open [http://localhost:5173](http://localhost:5173)
- Expected: Login page displayed

**Database Check**:
```bash
python -c "from src.database import SessionLocal; db = SessionLocal(); print('Database connected')"
```

---

## API Documentation

### Swagger Interactive Docs

Once backend is running, visit:
```
http://localhost:8000/docs
```

Features:
- Try out API endpoints directly
- View all request/response schemas
- Test authentication (login → copy access_token)

### ReDoc Alternative Documentation

```
http://localhost:8000/redoc
```

### Sample API Calls

**Login (Get JWT Token)**:
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin_alice",
    "password": "SecurePassword123"
  }'

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "refresh_token": "...",
#   "expires_in": 900,
#   "user": {...}
# }
```

**Get Anomalies (with token)**:
```bash
curl -X GET "http://localhost:8000/api/anomalies?page=1&per_page=10" \
  -H "Authorization: Bearer <access_token>"
```

---

## Testing

### Backend Unit Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_auth.py -v

# Run only fast tests (skip integration)
pytest -m "not integration" -v
```

**Test Structure**:
```
backend/
  tests/
    unit/          # Fast, isolated tests
    integration/   # Database + API tests
    contract/      # API contract validation
```

**Coverage Requirement**: 80%+ (per Constitution)

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- anomalies.test.jsx
```

**Test Structure**:
```
frontend/
  tests/
    unit/          # Component + hook tests
    integration/   # API mocking + full page tests
```

### End-to-End Testing (Recommended for Pre-deployment)

```bash
# Install Playwright (E2E testing tool)
cd frontend
npm install -D @playwright/test

# Run E2E tests
npx playwright test

# View test report
npx playwright show-report
```

**E2E Scenarios** (to be created):
1. User login → view dashboard → filter anomalies
2. Admin login → upload model → verify activation
3. Manager view → export report (v1.1)

---

## Troubleshooting

### Backend Issues

**Issue: Python 3.12 not found**
```bash
# Solution: Use pyenv or install specific version
python3.12 --version
# If not available, download from python.org
```

**Issue: `ModuleNotFoundError: No module named 'fastapi'`**
```bash
# Solution: Run uv sync
uv sync
# Or activate venv first
source .venv/bin/activate  # macOS/Linux
.\.venv\Scripts\activate   # Windows
```

**Issue: Database locked (SQLite)**
```bash
# Solution: Close all connections and remove .db file
rm backend/anomaly.db
python scripts/init_db.py  # Reinitialize
```

**Issue: Port 8000 already in use**
```bash
# Solution: Use different port
uvicorn src.main:app --reload --port 8001
# Update frontend .env.local: VITE_API_BASE_URL=http://localhost:8001/api
```

### Frontend Issues

**Issue: Blank page / 404 on localhost:5173**
```bash
# Solution: Verify dev server started
npm run dev
# Check for build errors in terminal
```

**Issue: CORS error when calling API**
```bash
# Solution: Verify CORS_ORIGINS in backend .env includes frontend URL
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
# Then restart backend
```

**Issue: `npm ERR! code ERESOLVE unable to resolve dependency tree`**
```bash
# Solution: Force dependency resolution
npm install --legacy-peer-deps
```

### Database Issues

**Issue: Database locked (SQLite with concurrent writes)**
```bash
# Solution: Use WAL mode
sqlite3 anomaly.db "PRAGMA journal_mode=WAL;"
```

**Issue: Migrations failed (Alembic)**
```bash
# Solution: Reset migrations
alembic downgrade base
alembic upgrade head
```

---

## Development Workflow

### Before Starting Development

```bash
# 1. Create feature branch
git checkout -b feature/anomaly-filters

# 2. Activate venv + sync deps
source .venv/bin/activate
uv sync

# 3. Start both servers
# Terminal 1: Backend
uvicorn src.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Watch tests
pytest --watch
npm test -- --watch
```

### Code Quality Checks

```bash
# Python linting + formatting
cd backend
ruff check --fix .
black .

# JavaScript linting + formatting
cd frontend
npm run lint -- --fix
npm run format

# Type checking
mypy src/  # Python
npm run type-check  # JavaScript
```

### Before Committing

```bash
# 1. Run all tests
pytest --cov=src
npm test -- --coverage

# 2. Verify coverage threshold (80%+)

# 3. Run linters
ruff check .
eslint .

# 4. Commit with message
git add .
git commit -m "feat(anomaly): add date range filter"

# 5. Push to branch
git push origin feature/anomaly-filters
```

---

## Production Deployment

### Database Setup (PostgreSQL)

```bash
# Install PostgreSQL 14+
# Create database
psql -U postgres -c "CREATE DATABASE anomaly_db;"

# Configure connection in .env
DATABASE_URL=postgresql://user:password@localhost/anomaly_db

# Run migrations
alembic upgrade head
python scripts/seed_categories.py
```

### Backend Production Build

```bash
cd backend

# Create .env.prod with production variables
# SECRET_KEY: Use `openssl rand -hex 32`
# DEBUG=False
# CORS_ORIGINS: Set to production domain only

# Build Docker image (optional)
docker build -t anomaly-detector:1.0.0 .

# Or run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 src.main:app
```

### Frontend Production Build

```bash
cd frontend

# Create .env.production with production API URL
VITE_API_BASE_URL=https://api.anomaly-detector.com

# Build static assets
npm run build

# Output: dist/ directory ready for deployment
ls dist/
```

### CI/CD Pipeline

See `.github/workflows/` for automated testing and deployment

---

## Next Steps

1. **Complete backend API**: Implement all endpoints in `src/api/`
2. **Complete frontend UI**: Build React components in `frontend/src/components/`
3. **Add integration tests**: Create E2E tests with Playwright
4. **Deploy to staging**: Verify on staging environment before production
5. **Setup monitoring**: Add error tracking (Sentry) and logging

---

## Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **React Docs**: https://react.dev/
- **Recharts Docs**: https://recharts.org/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **Pytest Docs**: https://docs.pytest.org/
- **Vitest Docs**: https://vitest.dev/

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section above
2. Review spec.md for design details
3. Check API docs at `/docs` endpoint
4. Create GitHub issue with error logs

---

**Ready to Start Coding?** ✅ All prerequisites met → proceed with feature implementation following tasks.md

