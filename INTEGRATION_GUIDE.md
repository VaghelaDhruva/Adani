# Integration Guide - Production Upgrade

## Quick Start

### 1. Database Migration

Run migrations to create new tables:

```bash
cd backend
alembic revision --autogenerate -m "Add job queue, RBAC, KPI tables"
alembic upgrade head
```

### 2. Update Main Application

Update `backend/app/main.py` to include new routes:

```python
from app.api.v1 import routes_optimize_v2  # New version

# Replace old route with new one
app.include_router(routes_optimize_v2.router, prefix=f"{settings.API_V1_STR}/optimize", tags=["optimize"])
```

### 3. Install Pyomo (if not already installed)

```bash
pip install pyomo
```

### 4. Update Frontend

Update React components to:
- Poll `/api/v1/optimize/{job_id}/status` instead of blocking
- Use precomputed KPI endpoints
- Implement RBAC route guards

### 5. Environment Variables

Add to `.env`:

```env
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///./clinker_supply_chain.db
```

### 6. Create Initial Users

```python
from app.db.models.user import User
from app.core.security import get_password_hash

# Create admin user
admin = User(
    user_id="admin001",
    username="admin",
    email="admin@company.com",
    hashed_password=get_password_hash("changeme"),
    role="admin",
    allowed_ius=None,  # Admin has access to all
    allowed_gus=None,
    is_active=True,
    is_superuser=True
)
```

## Key Changes Summary

### Backend Changes
1. **New Job Queue System** - `app/services/job_queue.py`
2. **Pyomo Optimizer** - `app/services/optimization/pyomo_optimizer.py`
3. **RBAC System** - `app/core/rbac.py`
4. **Data Validation** - `app/services/data_validation.py`
5. **KPI Precomputation** - `app/services/kpi_precomputation.py`
6. **Currency Utilities** - `app/utils/currency.py`

### Database Changes
1. **New Tables:**
   - `job_status` - Job tracking
   - `users` - User management
   - `roles` - Role definitions
   - `user_sessions` - Session tracking
   - `kpi_precomputed` - Precomputed KPIs
   - `kpi_aggregated` - Aggregated KPIs
   - `scenarios` - Scenario management
   - `scenario_comparison` - Scenario comparison

2. **Updated Tables:**
   - `audit_log` - Added user_id relationship
   - `optimization_run` - Enhanced with validation fields

### API Changes
1. **New Endpoints:**
   - `POST /api/v1/optimize` - Submit job (non-blocking)
   - `GET /api/v1/optimize/{job_id}/status` - Poll status
   - `GET /api/v1/optimize/{job_id}/results` - Get results
   - `POST /api/v1/optimize/{job_id}/cancel` - Cancel job

2. **Updated Endpoints:**
   - All endpoints now support RBAC
   - Data filtering by user access

## Testing Checklist

- [ ] Job queue creates jobs correctly
- [ ] Optimization runs in background
- [ ] Status polling works
- [ ] Results are stored correctly
- [ ] KPIs are precomputed
- [ ] Dashboard loads quickly
- [ ] RBAC restricts access correctly
- [ ] Currency formatting works
- [ ] Data validation catches errors
- [ ] Scenarios can be compared

## Rollback Plan

If issues occur:

1. **Revert Routes:**
   ```python
   # Use old routes_optimize.py instead of routes_optimize_v2.py
   ```

2. **Database Rollback:**
   ```bash
   alembic downgrade -1
   ```

3. **Keep Old Optimizer:**
   - Old `optimization_engine.py` still works
   - Can switch back if Pyomo issues occur

## Support

For issues or questions:
- Check `PRODUCTION_READINESS_REVIEW.md` for architecture details
- Review logs in `backend/logs/`
- Check job status in `job_status` table

