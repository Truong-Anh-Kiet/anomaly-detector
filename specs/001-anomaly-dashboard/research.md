# Research: Anomaly Detection Dashboard Tech Stack

**Date**: 2026-03-11  
**Feature**: Anomaly Detection Dashboard  
**Session**: Implementation Planning Phase 0

---

## Research Task 1: FastAPI + JWT Authentication Architecture

### Decision: FastAPI + python-jose for JWT Auth

**Rationale**: 
- FastAPI has native async support + automatic OpenAPI docs (useful for debugging)
- python-jose is battle-tested for JWT encoding/decoding in Python microservices
- FastAPI's Depends injection pattern is cleaner than decorator-based RBAC alternatives
- Fastapi middleware integrates seamlessly with existing request/response pipelines

**Implementation Pattern**:

```python
# dependencies.py: JWT verify + role extraction
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

async def get_current_user(credentials: HTTPAuthCredentials = Depends(HTTPBearer())) -> User:
    token = credentials.credentials
    payload = jose.jwt.get_unverified_claims(token)  # Decode without verification first
    user_id = payload.get("sub")
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user: raise HTTPException(status_code=401, detail="Invalid token")
    return user

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

**RBAC at Endpoint Level**:
```python
# api/anomalies.py
@router.get("/anomalies")
async def list_anomalies(
    current_user: User = Depends(get_current_user),
    category: str = None,
    date_from: date = None
):
    # Filter based on role
    if current_user.role == RoleEnum.ANALYST:
        # Only own categories
        query = query.filter(AnomalyDetectionResult.category.in_(current_user.assigned_categories))
    else:
        # Manager/Admin see all
        pass
    return results
```

**Alternatives Rejected**:
- `fastapi-rbac` (3rd party, less flexibility)
- Manual decorator-based checks (boilerplate, harder to test)

**Decision**: ✅ **Use python-jose + custom Depends for RBAC**

---

### Decision: SQLite for MVP, PostgreSQL for Production

**Rationale**:
- SQLite: Zero-config, file-based, perfect for MVP + rapid testing
- Can migrate to PostgreSQL later by changing only connection string + Docker Compose
- SQLAlchemy ORM abstracts DB details; Alembic migrations make schema changes reversible

**MVP Trade-off**: 
- SQLite limitations (single writer) are acceptable for daily batch + API reads
- If concurrent users exceed 10, upgrade to PostgreSQL (documented in roadmap)

**Decision**: ✅ **SQLite for MVP, PostgreSQL-ready via SQLAlchemy**

---

## Research Task 2: React Time Series Charting & Filtering

### Decision: Recharts for Time Series + React Hook Form for Filters

**Rationale - Recharts**:
- Declarative, React-native (components, not canvas), responsive by default
- Recharts ComposedChart supports line + scatter points (perfect for highlighting anomalies)
- Built-in responsive container + tooltip interactions
- 30KB gzipped (within budget)

**Rationale - React Hook Form**:
- Zero-dependency form library (critical for bundle size <500KB)
- Integrates seamlessly with filter state (date pickers, dropdowns, checkboxes)
- Non-controlled component approach = fast filter updates

**Filtering Pattern**:

```typescript
// useFilters.ts
export function useFilters() {
  const { register, watch } = useForm({
    defaultValues: {
      dateFrom: new Date(Date.now() - 90*24*60*60*1000),  // 90 days
      dateTo: new Date(),
      categories: [],  // Multi-select
      severity: [],
      anomalyType: []
    }
  });
  
  const filters = watch();  // Real-time filter object
  return { filters, register };
}

// AnomalyFilters.tsx
export function AnomalyFilters() {
  const { filters, register } = useFilters();
  const { data } = useAnomalies(filters);  // Refetch on any filter change
  
  return (
    <div>
      <input {...register("dateFrom")} type="date" />
      <select {...register("categories", { setValueAs: v => v.split(',') })} multiple />
      {/* Results auto-update */}
    </div>
  );
}
```

**Alternatives Rejected**:
- Apache ECharts (too large + steeper learning curve)
- Plotly (overkill for line + scatter charts; large bundle)

**Decision**: ✅ **Recharts + React Hook Form**

---

### Decision: Pagination + Lazy Loading for Large Datasets

**Rationale**:
- Financial data can have 10000+ daily anomalies; loading all at once = sluggish UI
- Pagination: Client fetches Page 1 (50 items); user clicks "Next" → Page 2
- Lazy Loading (Intersection Observer): As user scrolls, auto-load next page

**Implementation**:
```typescript
// useAnomalies.ts
const [page, setPage] = useState(1);
const { data, fetchNextPage, hasMore } = useQuery({
  queryKey: ['anomalies', filters, page],
  queryFn: () => api.get(`/api/anomalies?page=${page}`, { params: filters })
});

// Component: Infinite scroll detection
<div ref={observerTarget} />  // When in viewport, fetchNextPage()
```

**Decision**: ✅ **Pagination (50 items/page) + Intersection Observer for lazy load**

---

## Research Task 3: Daily Batch Job Scheduling

### Decision: APScheduler (over Celery for MVP) for Simplicity

**Rationale**:
- Celery requires separate Redis/RabbitMQ broker; overkill for single daily job
- APScheduler integrates directly into FastAPI process; configuration is just a dict
- Cron syntax `0 2 * * *` = 2:00 AM daily; familiar to DevOps/SRE

**Implementation**:

```python
# src/batch_scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', hour=2, minute=0, id='daily_batch')
def daily_batch_job():
    import_csv()  # Load new transactions
    run_inference()  # Detect anomalies
    save_results()  # Persist to DB

# src/main.py
scheduler.start()  # Start on app startup
```

**Manual Trigger Support** (for testing):
```python
@router.post("/api/admin/batch/run")
async def trigger_batch(current_user: User = Depends(get_admin_user)):
    daily_batch_job()
    return {"status": "Batch executed"}
```

**Alternatives Rejected**:
- Celery (too complex for MVP; can add in v1.1 if needed)
- Kubernetes CronJob (requires k8s; not viable for MVP on single server)

**Decision**: ✅ **APScheduler for daily 2:00 AM batch; manual trigger via Admin API**

---

## Research Task 4: Audit Logging & 1-Year Retention Policy

### Decision: SQLite/PostgreSQL AuditLog Table + Cron Cleanup Job

**Schema**:
```sql
CREATE TABLE audit_log (
  log_id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  action VARCHAR(50),  -- LOGIN, EXPORT, RETRAIN_MODEL
  resource_type VARCHAR(50),  -- Anomaly, User, Model
  resource_id UUID,
  details JSONB,  -- Context-specific metadata
  timestamp DATETIME DEFAULT NOW(),
  archived_at DATETIME,  -- Set to NOW() after 365 days
  created_at DATETIME DEFAULT NOW()
);

CREATE INDEX idx_audit_user_ts ON audit_log(user_id, timestamp);
CREATE INDEX idx_audit_archived ON audit_log(archived_at);  -- For cleanup
```

**Retention Policy**:
1. Days 0-365: `archived_at IS NULL` (active logs, searchable)
2. Day 366: Cron job sets `archived_at = NOW()` (soft-deleted, hidden from UI)
3. Day 730: Cron job hard-deletes `WHERE archived_at < DATE_SUB(NOW(), INTERVAL 365 DAY)`

**Implementation**:

```python
# src/services/audit_logger.py
async def log_action(user_id: UUID, action: str, resource_type: str, resource_id: UUID = None):
    entry = AuditLog(
        log_id=uuid.uuid4(),
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        timestamp=datetime.utcnow(),
        archived_at=None  # Active
    )
    db.add(entry)
    db.commit()

# src/batch_scheduler.py - Archive older than 365 days
@scheduler.scheduled_job('cron', hour=3, minute=0, id='archive_logs')
def archive_old_logs():
    cutoff = datetime.utcnow() - timedelta(days=365)
    db.query(AuditLog).filter(
        AuditLog.created_at < cutoff,
        AuditLog.archived_at.is_(None)
    ).update({'archived_at': datetime.utcnow()})
    
    # Hard delete logs older than 2 years
    very_old = datetime.utcnow() - timedelta(days=730)
    db.query(AuditLog).filter(AuditLog.archived_at < very_old).delete()
    db.commit()
```

**Alternatives Rejected**:
- TimescaleDB (specialized for time-series; overkill)
- Custom archival to S3 (introduces complexity; SQLite/PostgreSQL native retention sufficient)

**Decision**: ✅ **SQLite/PostgreSQL AuditLog + cron soft-delete (365d) / hard-delete (730d)**

---

## Research Task 5: Hybrid Statistical + ML Anomaly Detection Model

### Decision: Two-Method Pipeline (Statistical + Isolation Forest) with Score Fusion

**Model Architecture** (from notebook analysis):

The notebook implements a sophisticated **hybrid detection system**:

1. **Statistical Method** (40% weight in fusion):
   - Rolling Median Absolute Deviation (MAD) over 12-day window
   - Modified Z-score: `0.6745 * (amount - rolling_median) / rolling_mad`
   - Threshold: `|modified_z| > 8` flags as statistical anomaly
   - Detects: Sudden spikes/drops, abrupt deviations from median
   - Output: `Stats_Score` (normalized 0-1)

2. **Machine Learning Method** (60% weight in fusion):
   - Isolation Forest (300 estimators) trained on engineered features
   - Window-based features: `[mean, std, slope, last_value, last_pct_change]` at multiple windows (3-day, 6-day)
   - Dynamic threshold: 99.999th percentile of training anomaly scores
   - Detects: Non-obvious patterns in feature space (trend changes, volatility shifts)
   - Output: `ML_Score` (normalized 0-1)

3. **Score Fusion**:
   - **Combined Score = 0.4 × Stats_Score_Normalized + 0.6 × ML_Score_Normalized**
   - Normalization: Both scores normalized by training period maximum
   - Final Threshold: 99.2nd percentile of training combined scores
   - Decision: "Anomaly" if Combined_Score > threshold (test period only)

4. **Cause Classification**:
   - If Stats_Score dominates → `cause = "statistical_spike"` (IQR deviation)
   - If ML_Score dominates → `cause = "ml_pattern_anomaly"` (feature space outlier)
   - If both high → `cause = "hybrid_confirmed"` (high confidence)
   - Aggregate anomalies → `cause = "system_level_anomaly"` (daily total spike)

**Rationale**:
- Neither method alone is sufficient (stats miss patterns, ML misses explicit spikes)
- 60% ML / 40% stats weighting from notebook tune; balances sensitivity/specificity
- Rolling statistics (not global) adapt to seasonal patterns in financial data
- Window features capture momentum/trend shifts ML algorithms exploit well
- Score normalization using training period max prevents score drift over time

**Implementation**:

```python
# src/ml/statistical_detector.py
class StatisticalAnomalyDetector:
    def __init__(self, rolling_window=12, mad_threshold=8):
        self.rolling_window = rolling_window
        self.mad_threshold = mad_threshold
    
    def rolling_mad(self, x):
        """Median Absolute Deviation"""
        med = np.median(x)
        return np.median(np.abs(x - med))
    
    def detect(self, series: np.array, category_history: pd.DataFrame) -> dict:
        # Compute rolling statistics
        rolling_median = category_history['Amount'].rolling(self.rolling_window).median().shift(1)
        rolling_mad_val = category_history['Amount'].rolling(self.rolling_window).apply(self.rolling_mad).shift(1)
        
        # Modified Z-score
        modified_z = 0.6745 * (series - rolling_median) / (rolling_mad_val + 1e-9)
        stats_score = abs(modified_z)
        is_anomaly = stats_score > self.mad_threshold
        
        return {
            'stats_score': stats_score,
            'modified_z': modified_z,
            'is_anomaly': is_anomaly,
            'rolling_median': rolling_median
        }

# src/ml/ml_detector.py
class MLAnomalyDetector:
    def __init__(self, model_path: str):
        self.model = joblib.load(model_path)  # Pre-trained Isolation Forest
        self.windows = [3, 6]  # Multiple window sizes
        self.feature_cols = ['mean', 'std', 'slope', 'last_value', 'last_pct_change']
    
    def create_window_features(self, amount_series: np.array, window_size: int) -> pd.DataFrame:
        """Extract rolling window features"""
        features = []
        for i in range(len(amount_series) - window_size + 1):
            window = amount_series[i:i+window_size]
            pct_change = (window[-1] - window[-2]) / (abs(window[-2]) + 1e-9) * 100
            features.append({
                'mean': window.mean(),
                'std': window.std(),
                'slope': np.polyfit(range(window_size), window, 1)[0],
                'last_value': window[-1],
                'last_pct_change': pct_change
            })
        return pd.DataFrame(features)
    
    def detect(self, category_history: pd.DataFrame) -> dict:
        # Extract features from multiple windows
        all_features = []
        for window_size in self.windows:
            features_df = self.create_window_features(category_history['Amount'].values, window_size)
            all_features.append(features_df)
        
        features_combined = pd.concat(all_features, ignore_index=True)
        
        # Score with Isolation Forest
        scores = -self.model.decision_function(features_combined[self.feature_cols])
        
        return {
            'ml_scores': scores,
            'decision_scores': scores,
            'features': features_combined
        }

# src/ml/score_fusion.py
class AnomalyScoreFusion:
    STATS_WEIGHT = 0.4
    ML_WEIGHT = 0.6
    
    def __init__(self, stats_threshold_percentile=99.2):
        self.stats_threshold_percentile = stats_threshold_percentile
    
    def fuse_scores(self, 
        stats_score: float, 
        ml_score: float, 
        stats_max_train: float, 
        ml_max_train: float
    ) -> dict:
        # Normalize by training period max
        stats_normalized = min(stats_score / (stats_max_train + 1e-9), 1.0)
        ml_normalized = min(ml_score / (ml_max_train + 1e-9), 1.0)
        
        # Fuse
        combined = self.STATS_WEIGHT * stats_normalized + self.ML_WEIGHT * ml_normalized
        
        # Determine cause
        if stats_normalized > ml_normalized:
            cause = 'statistical_spike'
        elif ml_normalized > stats_normalized:
            cause = 'ml_pattern_anomaly'
        else:
            cause = 'hybrid_confirmed' if combined > 0.7 else 'normal'
        
        return {
            'combined_score': combined,
            'stats_score': stats_score,
            'ml_score': ml_score,
            'cause': cause
        }

# src/services/anomaly_service.py
class AnomalyDetectionService:
    def __init__(self, model_path: str, stats_model_metrics: dict):
        self.stats_detector = StatisticalAnomalyDetector()
        self.ml_detector = MLAnomalyDetector(model_path)
        self.fusion = AnomalyScoreFusion()
        
        # Threshold from training period (stored in ModelVersion.metrics)
        self.stats_threshold = stats_model_metrics['stats_max_train']
        self.ml_threshold = stats_model_metrics['ml_max_train']
        self.combined_threshold = stats_model_metrics['combined_threshold']
    
    def detect(self, transaction: Transaction, category_history: pd.DataFrame) -> AnomalyDetectionResult:
        # 1. Statistical detection
        stats_result = self.stats_detector.detect(transaction.amount, category_history)
        stats_score = stats_result['stats_score']
        
        # 2. ML detection
        ml_result = self.ml_detector.detect(category_history)
        ml_score = ml_result['ml_scores'][-1]  # Last window score
        
        # 3. Fuse scores
        fusion_result = self.fusion.fuse_scores(stats_score, ml_score, self.stats_threshold, self.ml_threshold)
        
        # 4. Final decision
        is_anomaly = fusion_result['combined_score'] > self.combined_threshold
        
        return AnomalyDetectionResult(
            transaction_id=transaction.id,
            stats_score=stats_score,
            ml_score=ml_score,
            combined_score=fusion_result['combined_score'],
            result='Anomaly' if is_anomaly else 'Normal',
            cause=fusion_result['cause'],
            explanation=self._generate_explanation(fusion_result),
            model_version=self.model_version
        )
    
    def _generate_explanation(self, fusion_result: dict) -> str:
        cause = fusion_result['cause']
        if cause == 'statistical_spike':
            return f"Z-score {fusion_result['stats_score']:.2f} exceeds threshold (>8): Abrupt deviation from rolling median"
        elif cause == 'ml_pattern_anomaly':
            return f"ML score {fusion_result['ml_score']:.2f} flagged unusual feature pattern in window features"
        elif cause == 'hybrid_confirmed':
            return f"Both statistical ({fusion_result['stats_score']:.2f}) and ML ({fusion_result['ml_score']:.2f}) methods flagged anomaly (HIGH CONFIDENCE)"
        else:
            return "Within normal bounds (both statistical and ML scores nominal)"
```

**ModelVersion.metrics Storage** (from training notebook):

```json
{
  "precision": 0.9524,
  "recall": 1.0,
  "f1_score": 0.9756,
  "training_date": "2026-03-11",
  "training_set_size": 600,
  "test_set_size": 100,
  "stats_max_train": 12.89,
  "ml_max_train": 0.8234,
  "combined_threshold": 0.4521,
  "rolling_window": 12,
  "mad_threshold": 8,
  "ml_windows": [3, 6],
  "weights": {"stats": 0.4, "ml": 0.6}
}
```

**Alternatives Rejected**:
- **Isolation Forest Only** (rejected): Misses explicit statistical spikes; ML-only systems have blind spots in rule-based detection
- **Statistical Only** (rejected): Fails to detect complex patterns in feature space; high false negatives on subtle anomalies
- **Simple Weighted Average** (rejected): Using 40/60 split is deliberate from notebook tune; different weights impact sensitivity/specificity tradeoff
- **MLflow/Model Registry** (rejected): Hybrid detection is custom; pickle + ModelVersion table sufficient for version tracking

**Unknowns Resolved**:
- **Model cold-start**: Load Isolation Forest + scaler at startup (GLOBAL_MODEL); ~50ms startup cost
- **Feature engineering at scale**: Pre-compute rolling statistics in batch job; cache window features for last 7 days
- **Threshold management**: Store all thresholds in ModelVersion.metrics; no hardcoding in code
- **Cause classification logic**: Determined by which method's score is higher; clear audit trail in explanation
- **System-level monitoring**: Apply same hybrid pipeline to daily total (aggregate all categories); separate threshold configuration
- **Score calibration**: Metrics from notebook training (precision 0.9524, recall 1.0) establish baseline; retrain only when metrics drift

---

## Summary: Tech Stack Decisions

| Area | Decision | Rationale | Alternatives |
|------|----------|-----------|--------------|
| **Backend Framework** | FastAPI | Async support, auto OpenAPI, native Depends | Flask (slower), Django (too heavy) |
| **Authentication** | python-jose JWT | Industry standard, simple stateless tokens | OAuth2 library (overkill), custom (risky) |
| **RBAC** | Custom Depends + role checks | Flexible, testable, no 3rd-party deps | fastapi-rbac (less flexible) |
| **Database** | SQLite (MVP) → PostgreSQL | Zero-config MVP, easy migration | MongoDB (wrong domain) |
| **Charting** | Recharts | React-native, responsive, 30KB | ECharts (large), Plotly (overkill) |
| **Form Filtering** | React Hook Form | Zero-dep, fast, seamless filters | Formik (boilerplate), Redux (overkill) |
| **Batch Scheduling** | APScheduler | Integrated, simple cron syntax, no broker | Celery (overkill), K8s CronJob (k8s-only) |
| **Audit Logging** | SQLite AuditLog table | Native SQL, 1-year retention policy + cron | TimescaleDB (specialized), custom archive (complex) |
| **Anomaly Detection** | Hybrid Statistical + ML (40% + 60%) | Statistical catches explicit spikes; ML finds patterns; balanced approach | Stats only (misses patterns), ML only (misses spikes), Single-method (blind spots) |

---

## Unknowns Resolved

| Unknown | Research Finding | Implementation Impact |
|---------|-----------------|---------------------:|
| JWT token expiry + refresh | Implement 15min access token + 7day refresh token | Requires refresh endpoint; frontend token refresh logic |
| Chart rendering with 365+ points | Recharts handles well; recommend data aggregation (daily bars) | Lazy load categories on-demand to avoid initial load bloat |
| CSV import from where? | Plan assumes file upload API endpoint; can integrate S3/external source later | File endpoint in Phase 2 |
| Hybrid statistical + ML implementation | Both methods run in parallel: stats via rolling MAD + modified Z-score; ML via Isolation Forest on engineered features | Requires two detector classes + fusion logic in anomaly_service.py |
| Score fusion weighting | Use 40% statistical + 60% ML (from notebook) | Weights stored in ModelVersion.metrics; retrievable per model version |
| Cause classification logic | Determine by which method's score dominates during fusion | Enables clear anomaly attribution (spike vs pattern vs confirmed) |
| Feature engineering at scale | Pre-compute rolling window features (3-day, 6-day windows) during batch job | Cache window features for last 7 days to support inference hot path |
| Model cold-start | Load Isolation Forest + StandardScaler at startup; ~50ms one-time cost | GLOBAL_MODEL cached in memory; subsequent calls negligible overhead |
| Threshold management | All thresholds (MAD=8, stats_max, ml_max, combined_threshold) stored in ModelVersion.metrics | Retrieved once on service init; no hardcoding in code ensures version-specific thresholds |
| System-level anomalies | Apply hybrid pipeline to aggregated daily totals (sum across all categories) | Separate AnomalyDetectionService instance tuned for system-level detection |

---

## Ready for Phase 1 Design

✅ **All research questions answered**
✅ **Tech stack decisions documented with rationale**
✅ **Trade-offs vs. alternatives clearly explained**
✅ **No blockers identified for implementation**

**Next Artifacts**:
- `data-model.md` — Entity relationships, schema, validation
- `contracts/` — API spec, roles, data schemas
- `quickstart.md` — Development environment setup

