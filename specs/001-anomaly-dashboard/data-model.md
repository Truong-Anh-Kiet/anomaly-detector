# Data Model: Anomaly Detection Dashboard

**Date**: 2026-03-11  
**Feature**: Anomaly Detection Dashboard  
**Created by**: Phase 1 Design (speckit.plan)  
**Database**: SQLite (MVP) / PostgreSQL (Production)

---

## Entity Relationship Diagram

```
┌─────────────────┐         ┌──────────────────────┐
│     User        │◄────┐   │   AuditLog           │
├─────────────────┤     │   ├──────────────────────┤
│ user_id (PK)    │     └───┤ user_id (FK)         │
│ username        │         │ log_id (PK)          │
│ password_hash   │         │ action               │
│ role (ENUM)     │         │ resource_type        │
│ created_at      │         │ resource_id          │
│ last_login      │         │ timestamp            │
│ assigned_cats[] │         │ archived_at          │
└─────────────────┘         │ created_at           │
         △                   └──────────────────────┘
         │
         │
    [Admin]                  ┌──────────────────────┐
     [Manager]               │  ModelVersion        │
     [Analyst]               ├──────────────────────┤
                             │ version_id (PK)      │
                             │ version_name         │
                             │ uploaded_by (FK→User)│
                             │ uploaded_at          │
                             │ is_active (BOOL)     │
                             │ model_path           │
                             │ metrics (JSON)       │
                             │ created_at           │
                             └──────────────────────┘

┌──────────────────┐     ┌──────────────────────────┐
│  Category        │◄────┤  Transaction             │
├──────────────────┤     ├──────────────────────────┤
│ category_id (PK)│     │ transaction_id (PK)      │
│ name             │     │ date                     │
│ description      │     │ category (FK)            │
└──────────────────┘     │ amount                   │
                         │ source (optional)        │
                         │ created_at               │
                         └──────────────────────────┘
                                   △
                                   │
                         ┌─────────────────────────┐
                         │ AnomalyDetectionResult  │
                         ├─────────────────────────┤
                         │ detection_id (PK)       │
                         │ transaction_id (FK-1:1) │
                         │ stats_score (0-1)       │
                         │ ml_score (0-1)          │
                         │ combined_score (0-1)    │
                         │ result (Normal/Anomaly) │
                         │ base_explanation        │
                         │ cause (ENUM)            │
                         │ advice                  │
                         │ model_version           │
                         │ created_at              │
                         └─────────────────────────┘
```

---

## Entity Definitions

### 1. User

**Purpose**: Authentication, authorization, audit trail

**Fields**:

| Column | Type | Constraint | Notes |
|--------|------|-----------|-------|
| user_id | UUID | PRIMARY KEY | Generated on creation |
| username | VARCHAR(255) | UNIQUE, NOT NULL | Login identifier |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hash, never plain text |
| role | ENUM(ADMIN, MANAGER, ANALYST) | NOT NULL | Determines API access level |
| assigned_categories | JSON ARRAY | DEFAULT [] | For Analyst role; null for Admin/Manager |
| created_at | DATETIME | DEFAULT NOW() | User creation timestamp |
| last_login | DATETIME | DEFAULT NULL | Updated on each successful login |
| is_active | BOOLEAN | DEFAULT TRUE | Soft-delete flag (archive without removing) |

**Validation Rules**:
- `username`: 3-50 characters, alphanumeric + underscore only
- `role`: Must be one of 3 enum values; Admin has full system access
- `assigned_categories`: Only populated for Analyst role; references Category.name
- `password_hash`: Must follow bcrypt cost factor ≥10 (for security)

**Indexes**:
```sql
CREATE UNIQUE INDEX idx_user_username ON user(username);
CREATE INDEX idx_user_role ON user(role);
```

**Relationships**:
- 1:N with AuditLog (user_id FK)
- 1:N with ModelVersion (uploaded_by FK)

---

### 2. Category

**Purpose**: Categorize financial transactions for grouped analysis

**Fields**:

| Column | Type | Constraint |
|--------|------|-----------|
| category_id | INT | PRIMARY KEY AUTO_INCREMENT |
| name | VARCHAR(255) | UNIQUE, NOT NULL |
| description | TEXT | DEFAULT NULL |

**Example Data**:
```
(1, "Average Fast Food format Check", "Average transaction amount in fast food sector")
(2, "Average check in Restaurant format", "Average check amount in restaurants")
(3, "Average consumer loan application", "Average consumer loan application amount")
(4, "Average pension", "Average pension payment")
(5, "Average spending in a fast food restaurant", "User spending at fast food restaurants")
(6, "Average spending in a restaurant", "User spending at restaurants")
...
```

**Validation Rules**:
- `name`: 5-255 characters; case-sensitive (preserve original financial category naming)
- Only Admin can add/edit categories (manual via API or seed script)

**Indexes**:
```sql
CREATE UNIQUE INDEX idx_category_name ON category(name);
```

**Relationships**:
- 1:N with Transaction (category_id FK)

---

### 3. Transaction

**Purpose**: Base financial transaction data from CSV imports

**Fields**:

| Column | Type | Constraint | Notes |
|--------|------|-----------|-------|
| transaction_id | UUID | PRIMARY KEY | Generated on import |
| date | DATE | NOT NULL | Transaction date (YYYY-MM-DD) |
| category | VARCHAR(255) | FOREIGN KEY | References Category.name |
| amount | FLOAT | NOT NULL | Transaction amount (e.g., 15.50) |
| source | VARCHAR(255) | DEFAULT NULL | Optional: data source identifier |
| created_at | DATETIME | DEFAULT NOW() | Import timestamp |

**Validation Rules**:
- `date`: Must be valid date; cannot be in future
- `category`: Must match existing Category.name
- `amount`: Must be numeric, typically positive (occasionally negative for reversals)
- Uniqueness: Combination of (date, category, amount) should not have duplicates in same batch (handle in import logic)

**Indexes**:
```sql
CREATE INDEX idx_transaction_date_category ON transaction(date, category);
CREATE INDEX idx_transaction_category ON transaction(category);
CREATE INDEX idx_transaction_date ON transaction(date);
```

**Relationships**:
- Foreign key to Category(name)
- 1:1 with AnomalyDetectionResult (detection_id FK)

---

### 4. AnomalyDetectionResult

**Purpose**: Output of anomaly detection algorithm; core diagnostic data

**Fields**:

| Column | Type | Constraint | Notes |
|--------|------|-----------|-------|
| detection_id | UUID | PRIMARY KEY | Generated post-inference |
| transaction_id | UUID | FOREIGN KEY UNIQUE | 1:1 with Transaction |
| stats_score | FLOAT | NOT NULL, CHECK (0-1) | Modified Z-score based |
| ml_score | FLOAT | NOT NULL, CHECK (0-1) | Isolation Forest score |
| combined_score | FLOAT | NOT NULL, CHECK (0-1) | 40% stats + 60% ML |
| result | ENUM(Normal, Anomaly) | NOT NULL | Final classification |
| base_explanation | TEXT | NOT NULL | Statistical + ML reasoning |
| cause | ENUM(...) | NOT NULL | Classification of anomaly type |
| advice | TEXT | NOT NULL | Actionable recommendation |
| model_version | VARCHAR(255) | NOT NULL | Tracks which model generated result |
| created_at | DATETIME | DEFAULT NOW() | Detection timestamp |

**Cause Enum Values** (derived from hybrid detection):
- `statistical_spike`: Statistical anomaly (|modified_z| > MAD_THRES=8) indicating abrupt deviation
- `statistical_drift`: Statistical trend anomaly detected via rolling statistics
- `ml_pattern_anomaly`: ML (Isolation Forest) detected pattern in windowed features (mean/std/slope/last_value)
- `hybrid_confirmed`: Both statistical AND ML methods flagged as anomaly (high confidence)
- `system_level_anomaly`: System-wide total exceeded threshold (aggregate of all categories)
- `normal`: No anomaly detected by either method

**Validation Rules**:
- `stats_score`, `ml_score`, `combined_score`: Must be between 0.0 and 1.0
- `result`: Derived as `combined_score > threshold` (threshold ≈ 0.914 from training data)
- `model_version`: Must match an existing ModelVersion.version_name
- All text fields (base_explanation, advice) must be non-empty
- One detection per transaction (enforced by UNIQUE constraint on transaction_id)

**Indexes**:
```sql
CREATE INDEX idx_detection_transaction ON anomaly_detection_result(transaction_id);
CREATE INDEX idx_detection_result ON anomaly_detection_result(result);
CREATE INDEX idx_detection_created ON anomaly_detection_result(created_at);
CREATE INDEX idx_detection_score ON anomaly_detection_result(combined_score);
CREATE INDEX idx_detection_cause ON anomaly_detection_result(cause);
```

**Relationships**:
- 1:1 with Transaction (transaction_id FK)

---

### 5. ModelVersion

**Purpose**: Track ML model versions for audit, versioning, and A/B testing

**Fields**:

| Column | Type | Constraint | Notes |
|--------|------|-----------|-------|
| version_id | UUID | PRIMARY KEY | Generated on upload |
| version_name | VARCHAR(255) | UNIQUE, NOT NULL | e.g., "model_v1709164234_anomaly_forest.pkl" |
| uploaded_by | UUID | FOREIGN KEY | User.user_id (must be Admin) |
| uploaded_at | DATETIME | DEFAULT NOW() | Upload timestamp |
| is_active | BOOLEAN | DEFAULT FALSE | Only one can be TRUE at a time |
| model_path | VARCHAR(255) | NOT NULL | File system or S3 path to .pkl |
| metrics | JSON | NOT NULL | Precision, Recall, F1 from training/validation |
| created_at | DATETIME | DEFAULT NOW() | Record creation timestamp |

**Example metrics JSON**:
```json
{
  "precision": 0.9524,
  "recall": 1.0,
  "f1_score": 0.9756,
  "training_date": "2026-03-11",
  "training_set_size": 600,
  "test_set_size": 100,
  "threshold": 0.914
}
```

**Validation Rules**:
- `version_name`: Must be unique; should include timestamp for traceability
- `uploaded_by`: Must be a User with role = ADMIN
- `is_active`: Only one row can have is_active = TRUE at any time (enforce with trigger or app logic)
- `metrics`: Must contain at minimum precision, recall, f1_score, training_date
- `model_path`: Must be accessible (verified on upload by loading model)

**Constraints**:
```sql
CREATE UNIQUE INDEX idx_model_version_name ON model_version(version_name);
CREATE INDEX idx_model_is_active ON model_version(is_active);
```

**Relationships**:
- Foreign key to User(user_id) via uploaded_by
- Referenced in AnomalyDetectionResult.model_version
- Used by AnomalyModel service to determine which .pkl to load

---

### 6. AuditLog

**Purpose**: Compliance, audit trail, 1-year retention policy

**Fields**:

| Column | Type | Constraint | Notes |
|--------|------|-----------|-------|
| log_id | UUID | PRIMARY KEY | Generated on action |
| user_id | UUID | FOREIGN KEY, NOT NULL | User performing action |
| action | VARCHAR(50) | NOT NULL | e.g., LOGIN, DOWNLOAD_EXPORT, RETRAIN_MODEL |
| resource_type | VARCHAR(50) | DEFAULT NULL | e.g., Anomaly, User, Model |
| resource_id | UUID | DEFAULT NULL | Specific resource affected |
| details | JSON | DEFAULT {} | Context-specific metadata |
| timestamp | DATETIME | NOT NULL | When action occurred |
| archived_at | DATETIME | DEFAULT NULL | Set to NOW() after 365 days (soft-delete) |
| created_at | DATETIME | DEFAULT NOW() | Log record creation time |

**Example Log Entries**:

```sql
-- User login
INSERT INTO audit_log (log_id, user_id, action, resource_type, timestamp)
VALUES (uuid(), 'user-123', 'LOGIN', 'User', NOW());

-- Anomaly viewed (for tracking user investigation)
INSERT INTO audit_log (log_id, user_id, action, resource_type, resource_id, details, timestamp)
VALUES (uuid(), 'user-456', 'VIEW_ANOMALY', 'Anomaly', 'detection-789', 
        '{"category": "Fast Food", "amount": 50.25}', NOW());

-- Model retrained
INSERT INTO audit_log (log_id, user_id, action, resource_type, resource_id, details, timestamp)
VALUES (uuid(), 'admin-001', 'RETRAIN_MODEL', 'Model', 'version-abc', 
        '{"model_version": "model_v12345.pkl", "precision": 0.95}', NOW());
```

**Action Enum** (non-exhaustive):
- `LOGIN` — User authentication successful
- `LOGOUT` — User session ended
- `VIEW_ANOMALY` — Accessed anomaly details
- `EXPORT_CSV` — Downloaded CSV report
- `DOWNLOAD_EXPORT` — Report generation
- `RETRAIN_MODEL` — Uploaded new model version
- `MANAGE_USER` — Created/edited/deleted user
- `MODIFY_CATEGORY` — Added/edited category

**Validation Rules**:
- `action`: Predefined enum list (enforce at app layer)
- `user_id`: Must reference existing User
- `resource_type` and `resource_id`: Either both present or both NULL
- `timestamp`: Should be <= created_at (action happens before log created)
- `archived_at`: Initially NULL; set to NOW() by archival cron job (365 days)

**Retention Policy**:

| Phase | Days | Condition | Action |
|-------|------|-----------|--------|
| Active | 0-365 | archived_at IS NULL | Searchable in UI, included in queries |
| Archived | 366-730 | archived_at IS NOT NULL | Hidden from UI, accessible via compliance reports |
| Deleted | 731+ | (hard delete) | Removed from database entirely |

**Indexes**:
```sql
CREATE INDEX idx_audit_user_timestamp ON audit_log(user_id, timestamp);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_archived ON audit_log(archived_at);  -- For cleanup cron
```

**Relationships**:
- Foreign key to User(user_id)

---

## Validation Rules Summary

| Entity | Rule | Enforcement |
|--------|------|-------------|
| User | username unique + 3-50 chars | DB unique + app validation |
| User | role in {ADMIN, MANAGER, ANALYST} | App enum validation |
| Category | name unique + 5-255 chars | DB unique + app validation |
| Transaction | date not future | App validation (import) |
| Transaction | category exists | DB foreign key + app validation |
| Transaction | amount is numeric | App type validation |
| AnomalyDetection | scores in [0, 1] | DB check constraint + app validation |
| AnomalyDetection | result in {Normal, Anomaly} | App enum validation |
| AnomalyDetection | cause in enum | App enum validation |
| AnomalyDetection | 1:1 with transaction | DB unique constraint |
| ModelVersion | one is_active = TRUE | App logic (update, don't insert/delete) |
| AuditLog | archived_at set after 365d | Cron job |

---

## State Transitions

### Transaction Lifecycle

```
CSV Import
    ↓
Transaction Created (date, category, amount)
    ↓
Anomaly Detector Service reads Transaction
    ↓
    ├→ Calculate stats_score (Z-score based)
    ├→ Calculate ml_score (Isolation Forest)
    ├→ Combine: 40% stats + 60% ML
    ├→ Classify: Normal or Anomaly
    ├→ Generate explanation + cause + advice
    ↓
AnomalyDetectionResult Created
    ↓
Dashboard displays result
```

### User Action → Audit Log

```
User Action (LOGIN, VIEW_ANOMALY, EXPORT_CSV, etc.)
    ↓
API Handler catches action
    ↓
Audit Logger service → INSERT into AuditLog
    ↓
    ├→ Days 1-365: archived_at = NULL (active)
    ├→ Days 366+: Cron job sets archived_at = NOW() (soft delete)
    ├→ Days 731+: Cron job hard deletes record
```

### Model Version Management

```
Admin uploads new model.pkl
    ↓
ModelVersion entry created with is_active = FALSE
    ↓
Admin confirms upload successful
    ↓
System sets old model is_active = FALSE, new is_active = TRUE
    ↓
System reloads GLOBAL_MODEL variable in-memory
    ↓
All new inferences use new model
    ↓
(Optionally, re-score historical anomalies with new model in v1.1)
```

---

## Migration Strategy

**MVP** (SQLite):
```sql
-- Single-file, no setup required
python scripts/init_db.py
# Creates all tables from SQLAlchemy models
```

**Production** (PostgreSQL):
```bash
# 1. Configure DATABASE_URL in .env
DATABASE_URL=postgresql://user:pass@localhost/anomaly_db

# 2. Run Alembic migrations
alembic upgrade head

# 3. Seed initial categories (one-time)
python scripts/seed_categories.py
```

**Migration from SQLite → PostgreSQL**:
```bash
# 1. Export SQLite to SQL dump
sqlite3 anomaly.db .dump > sqlite_dump.sql

# 2. Extract relevant tables(user, category, transaction, anomaly_detection_result, audit_log, model_version)

# 3. Adapt for PostgreSQL (UUID generation, timestamp functions)

# 4. Import into PostgreSQL
psql anomaly_db < adapted_dump.sql

# 5. Reindex
REINDEX DATABASE anomaly_db;
```

---

## ER Diagram SQL

```sql
-- Full schema generation (SQLAlchemy will handle this in code)
-- Below is the equivalent SQL for reference

CREATE TABLE user (
    user_id CHAR(36) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('ADMIN', 'MANAGER', 'ANALYST') NOT NULL,
    assigned_categories JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE category (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE transaction (
    transaction_id CHAR(36) PRIMARY KEY,
    date DATE NOT NULL,
    category VARCHAR(255) NOT NULL,
    amount FLOAT NOT NULL,
    source VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category) REFERENCES category(name),
    INDEX idx_transaction_date_category (date, category)
);

CREATE TABLE anomaly_detection_result (
    detection_id CHAR(36) PRIMARY KEY,
    transaction_id CHAR(36) UNIQUE NOT NULL,
    stats_score FLOAT NOT NULL CHECK (stats_score BETWEEN 0 AND 1),
    ml_score FLOAT NOT NULL CHECK (ml_score BETWEEN 0 AND 1),
    combined_score FLOAT NOT NULL CHECK (combined_score BETWEEN 0 AND 1),
    result ENUM('Normal', 'Anomaly') NOT NULL,
    base_explanation TEXT NOT NULL,
    cause ENUM('sudden_spike', 'sudden_drop', 'sharp_change', 'gradual_drift', 'high_volatility_drift', 'normal') NOT NULL,
    advice TEXT NOT NULL,
    model_version VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transaction(transaction_id),
    INDEX idx_detection_result (result),
    INDEX idx_detection_score (combined_score)
);

CREATE TABLE model_version (
    version_id CHAR(36) PRIMARY KEY,
    version_name VARCHAR(255) UNIQUE NOT NULL,
    uploaded_by CHAR(36) NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE,
    model_path VARCHAR(255) NOT NULL,
    metrics JSON NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES user(user_id),
    INDEX idx_model_is_active (is_active)
);

CREATE TABLE audit_log (
    log_id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id CHAR(36),
    details JSON,
    timestamp DATETIME NOT NULL,
    archived_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id),
    INDEX idx_audit_user_timestamp (user_id, timestamp),
    INDEX idx_audit_archived (archived_at)
);
```

---

## Ready for API Contract Definition

✅ **All entities defined with fields, validation, constraints**
✅ **Relationships documented (Foreign Keys, cardinality)**
✅ **State transitions clarified**
✅ **Migration strategy established**

**Next Artifact**: `contracts/` folder with API endpoints and data schemas

