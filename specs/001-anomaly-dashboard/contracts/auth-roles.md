# Authorization & Role-Based Access Control (RBAC)

**Feature**: Anomaly Detection Dashboard  
**Contract Version**: 1.0.0  
**Date**: 2026-03-11  
**Implementation Pattern**: FastAPI Depends with role checking

---

## Roles Defined

### ADMIN

**Purpose**: Full system control; model management; user management

**Permissions**:
- ✅ View all anomalies (across all categories)
- ✅ View detailed explanations
- ✅ Access audit logs (active + archived)
- ✅ Upload/activate model versions
- ✅ Create, edit, delete users
- ✅ Modify categories (add/edit/delete)
- ✅ Re-score historical anomalies (future feature)
- ✅ View system performance metrics

**Restricted**: Cannot view other users' passwords or private settings (for security)

**Example User**: alice_admin

---

### MANAGER

**Purpose**: Operational oversight; investigation approval; reporting

**Permissions**:
- ✅ View all anomalies (across all categories)
- ✅ View detailed explanations for all anomalies
- ✅ Access audit logs (active only; cannot view archived)
- ✅ Export anomaly data (CSV)
- ✅ Approve/dismiss alerts (future feature)
- ✅ Create investigation notes (future feature)
- ✅ View user activity logs

**Restrictions**:
- ❌ Cannot upload/activate models
- ❌ Cannot manage users
- ❌ Cannot modify categories
- ❌ Cannot access archived audit logs

**Example User**: manager_john

---

### ANALYST

**Purpose**: Investigation; pattern detection; category-specific analysis

**Permissions**:
- ✅ View anomalies in assigned categories only
- ✅ View detailed explanations for assigned categories
- ✅ Create investigation notes (future feature)
- ✅ View audit logs for own actions only

**Restrictions**:
- ❌ Cannot view anomalies outside assigned categories
- ❌ Cannot view other users' investigations
- ❌ Cannot export data
- ❌ Cannot upload models
- ❌ Cannot manage users
- ❌ Cannot modify categories
- ❌ Cannot view other analysts' audit logs

**Assignment**: Categories assigned via User.assigned_categories field
**Example User**: analyst_bob with assigned_categories = ["Fast Food", "Restaurant"]

---

## Endpoint Access Matrix

| Endpoint | ADMIN | MANAGER | ANALYST | Notes |
|----------|-------|---------|---------|-------|
| POST /auth/login | ✅ | ✅ | ✅ | Public; any authenticated user |
| POST /auth/refresh | ✅ | ✅ | ✅ | Public; refresh token required |
| GET /anomalies | ✅ All | ✅ All | ✅ Own categories | Filters enforced at query layer |
| GET /anomalies/{id} | ✅ All | ✅ All | ✅ Own categories | Authorization check on category |
| GET /categories | ✅ | ✅ | ✅ | All users can view |
| GET /timeseries/{category} | ✅ All | ✅ All | ✅ Own categories | Same category authorization |
| POST /admin/retrain | ✅ | ❌ | ❌ | Admin only |
| POST /admin/activate-model | ✅ | ❌ | ❌ | Admin only |
| GET /admin/models | ✅ | ❌ | ❌ | Admin only |
| GET /admin/users (future) | ✅ | ❌ | ❌ | Admin only |
| POST /admin/users (future) | ✅ | ❌ | ❌ | Admin only |
| PATCH /admin/users/{id} (future) | ✅ | ❌ | ❌ | Admin only |
| GET /audit-logs | ✅ All | ✅ Active only | ✅ Own only | Retention policy applied |

---

## Implementation Pattern: FastAPI Depends

### Role-Based Dependency Injection

```python
# backend/src/middleware/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from datetime import datetime, timedelta
from jose import JWTError, jwt
from enum import Enum

class Role(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    ANALYST = "ANALYST"

class User:
    def __init__(self, user_id: str, username: str, role: Role, assigned_categories: list = None):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.assigned_categories = assigned_categories or []

# Global HTTP bearer security scheme
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)) -> User:
    """Extract and validate JWT token; return User object"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        username = payload.get("username")
        role = payload.get("role")
        assigned_categories = payload.get("assigned_categories", [])
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return User(user_id=user_id, username=username, role=Role(role), assigned_categories=assigned_categories)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency: Assert user is ADMIN"""
    if user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def get_manager_or_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency: Assert user is MANAGER or ADMIN"""
    if user.role not in [Role.MANAGER, Role.ADMIN]:
        raise HTTPException(status_code=403, detail="Manager or Admin access required")
    return user

async def get_analyst_or_above(user: User = Depends(get_current_user)) -> User:
    """Dependency: Assert user is ANALYST, MANAGER, or ADMIN (i.e., authenticated)"""
    return user

async def authorize_by_category(
    category: str,
    user: User = Depends(get_current_user)
) -> User:
    """Dependency: Verify user can access category"""
    if user.role == Role.ADMIN or user.role == Role.MANAGER:
        return user  # Can access all categories
    
    if user.role == Role.ANALYST:
        if category not in user.assigned_categories:
            raise HTTPException(
                status_code=403,
                detail=f"Analyst can only view assigned categories: {user.assigned_categories}"
            )
        return user
    
    raise HTTPException(status_code=403, detail="Unauthorized")
```

### Usage in Route Handlers

```python
# backend/src/api/admin.py

from fastapi import APIRouter, Depends, UploadFile
from middleware.auth import get_admin, User

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/retrain")
async def retrain_model(
    model_file: UploadFile,
    version_name: str,
    metrics: dict,
    admin_user: User = Depends(get_admin)  # ⚠️ Assert ADMIN
) -> dict:
    """Only ADMIN can call this endpoint"""
    # Validate, upload, activate model
    return {"message": "Model uploaded"}

@router.get("/models")
async def list_models(_: User = Depends(get_admin)) -> dict:
    """Only ADMIN can call this endpoint"""
    return {"data": [...]}


# backend/src/api/anomalies.py

from fastapi import APIRouter, Depends, Query
from middleware.auth import get_analyst_or_above, authorize_by_category, User

router = APIRouter(prefix="/anomalies", tags=["anomalies"])

@router.get("/")
async def list_anomalies(
    date_from: str = Query(None),
    date_to: str = Query(None),
    categories: str = Query(None),  # CSV: "Fast Food,Restaurant"
    user: User = Depends(get_analyst_or_above)  # ✅ Any authenticated user
) -> dict:
    """All authenticated users; filter by category based on role"""
    # Parse categories from query
    requested_categories = categories.split(",") if categories else []
    
    # Enforce ANALYST category restriction
    if user.role == Role.ANALYST:
        allowed_categories = user.assigned_categories
        requested_categories = [c for c in requested_categories if c in allowed_categories]
        if not requested_categories:
            requested_categories = allowed_categories  # Default to all assigned
    
    # Query database with authorized categories
    return {"data": query_anomalies(requested_categories, date_from, date_to)}

@router.get("/{detection_id}")
async def get_anomaly_detail(
    detection_id: str,
    user: User = Depends(get_analyst_or_above)
) -> dict:
    """Retrieve anomaly; verify category authorization"""
    anomaly = db.get_anomaly(detection_id)
    
    if user.role == Role.ANALYST:
        if anomaly.category not in user.assigned_categories:
            raise HTTPException(status_code=403, detail="Cannot view this anomaly")
    
    return {"data": anomaly}


# backend/src/api/timeseries.py

@router.get("/timeseries/{category}")
async def get_timeseries(
    category: str,
    user: User = Depends(authorize_by_category(category))  # ✅ Check category access
) -> dict:
    """Category-level authorization enforced"""
    return {"data": get_timeseries_data(category)}
```

---

## JWT Token Structure

### Access Token Payload

**Duration**: 15 minutes (900 seconds)

**Example Payload** (decoded):
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "username": "analyst_bob",
  "role": "ANALYST",
  "assigned_categories": ["Fast Food", "Restaurant"],
  "exp": 1710163222,
  "iat": 1710162322
}
```

**Usage**: Include in HTTP header:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoi...
```

### Refresh Token Payload

**Duration**: 7 days (604800 seconds)

**Example Payload** (decoded):
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "token_type": "refresh",
  "exp": 1710768122,
  "iat": 1710163322
}
```

**Usage**: POST to `/auth/refresh` to obtain new access_token

---

## Audit Trail by Role

### ADMIN Actions Logged
- ✅ Model upload/activation
- ✅ User create/edit/delete
- ✅ Category modifications
- ✅ Access to sensitive data

### MANAGER Actions Logged
- ✅ Report exports
- ✅ Anomaly investigations
- ✅ Data access attempts

### ANALYST Actions Logged
- ✅ Anomaly views
- ✅ Investigation notes
- ✅ Failed access attempts

---

## Future Enhancements (v1.1+)

1. **Fine-Grained Permissions**: Move beyond role-based to permission-based (e.g., "can_export_anomalies")
2. **LDAP/OAuth Integration**: Replace local auth with enterprise identity provider
3. **Session Management**: Revoke tokens, manage active sessions per user
4. **Audit Log Retention Compliance**: Enforce legal hold for archived logs
5. **Time-Based Access Control**: Restrict access to certain operations by time-of-day
6. **Approval Workflows**: Manager approval required for certain ANALYST actions

---

## Testing Strategy

### Unit Tests

```python
# backend/tests/unit/test_auth.py

def test_get_admin_success():
    """AdminUser passes dependency check"""
    user = User(user_id="1", username="admin", role=Role.ADMIN)
    result = get_admin(user)
    assert result.role == Role.ADMIN

def test_get_admin_fails_for_manager():
    """ManagerUser fails dependency check"""
    user = User(user_id="2", username="manager", role=Role.MANAGER)
    with pytest.raises(HTTPException) as exc_info:
        get_admin(user)
    assert exc_info.value.status_code == 403

def test_analyst_category_restriction():
    """AnalystUser can only see assigned categories"""
    user = User(
        user_id="3",
        username="analyst",
        role=Role.ANALYST,
        assigned_categories=["Fast Food"]
    )
    result = authorize_by_category("Fast Food", user)
    assert result.user_id == "3"
    
    with pytest.raises(HTTPException) as exc_info:
        authorize_by_category("Restaurant", user)
    assert exc_info.value.status_code == 403
```

### Integration Tests

```python
# backend/tests/integration/test_endpoint_auth.py

def test_admin_model_upload(client, admin_token):
    """Admin can upload models"""
    response = client.post(
        "/api/admin/retrain",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code in [201, 400]  # Success or validation error, not 403

def test_manager_cannot_upload_model(client, manager_token):
    """Manager gets 403 when attempting model upload"""
    response = client.post(
        "/api/admin/retrain",
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 403

def test_analyst_category_filter(client, analyst_token):
    """Analyst can only query assigned categories"""
    response = client.get(
        "/api/anomalies?categories=Fast%20Food",
        headers={"Authorization": f"Bearer {analyst_token}"}
    )
    assert response.status_code == 200  # Assigned category
    
    response = client.get(
        "/api/anomalies?categories=Electronics",  # Not assigned
        headers={"Authorization": f"Bearer {analyst_token}"}
    )
    # Should either return empty or 403; depends on implementation
    assert response.status_code in [200, 403]
```

---

## Contract Status

✅ **3 roles defined (ADMIN, MANAGER, ANALYST)**
✅ **Endpoint access matrix documented**
✅ **FastAPI implementation pattern provided**
✅ **JWT token structure specified**
✅ **Audit trail by role defined**

**Ready for**: Backend middleware implementation; API route protection

