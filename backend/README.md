# Backend - Anomaly Detection Dashboard API

FastAPI-based REST API for anomaly detection with hybrid statistical and ML-based methods.

## Setup

### Prerequisites

- Python 3.12+
- UV package manager

### Installation

1. Install dependencies using UV:
```bash
cd backend
uv sync
```

2. Create `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

3. Run migrations (if using Alembic):
```bash
alembic upgrade head
```

### Running the Server

Development mode with auto-reload:
```bash
uv run uvicorn src.main:app --reload
```

Production mode:
```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

API documentation available at `http://localhost:8000/docs`

## Project Structure

```
backend/
├── src/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings and configuration
│   ├── database.py          # Database connection and initialization
│   ├── dependencies.py      # FastAPI dependencies
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # Business logic (use cases)
│   ├── api/                 # API route handlers
│   ├── middleware/          # Cross-cutting concerns
│   ├── ml/                  # ML model interface
│   └── utils/               # Helper functions
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── conftest.py         # Pytest configuration and fixtures
├── pyproject.toml          # Project metadata and dependencies
└── README.md               # This file
```

## Testing

Run all tests:
```bash
uv run pytest
```

Run with coverage:
```bash
uv run pytest --cov=src --cov-report=html
```

Run unit tests only:
```bash
uv run pytest tests/unit -m unit
```

Run integration tests only:
```bash
uv run pytest tests/integration -m integration
```

## Code Quality

Format code with Black:
```bash
uv run black src tests
```

Lint with Ruff:
```bash
uv run ruff check src tests
```

Type checking with Mypy:
```bash
uv run mypy src
```

## API Endpoints

### Authentication
- `POST /auth/login` - Login user, get JWT tokens
- `POST /auth/refresh` - Refresh access token

### Anomalies
- `GET /anomalies` - List anomalies with filtering and pagination
- `GET /anomalies/{id}` - Get anomaly detail
- `GET /categories` - List all financial categories
- `GET /timeseries/{category}` - Get historical timeseries data for chart

### Admin
- `POST /admin/models/upload` - Upload new ML model
- `GET /admin/models` - Get model version history
- `POST /admin/models/{id}/activate` - Activate model version
- `POST /admin/batch/trigger` - Manually trigger batch processing
- `GET /admin/batch/status` - Check batch job status
- `GET /admin/audit-logs` - View audit log history

See [API Docs](http://localhost:8000/docs) for full endpoint specifications.

## Configuration

Environment variables (see `.env.example`):

- `DATABASE_URL` - SQLite or PostgreSQL connection string
- `JWT_SECRET_KEY` - Secret key for JWT encoding (change in production!)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - Access token expiry (default 15)
- `BATCH_JOB_HOUR`, `BATCH_JOB_MINUTE` - Daily batch job schedule (default 2:00 AM UTC)
- `MODEL_PATH` - Path to trained ML model file
- `CORS_ORIGINS` - Comma-separated list of allowed CORS origins

## Development Guide

See [DEPLOYMENT.md](../DEPLOYMENT.md) for production deployment instructions.

## License

MIT
