# Architecture Overview

## System Layers

1. **Data Layer**
   - CSV/Excel upload via FastAPI
   - PostgreSQL storage with SQLAlchemy models
   - External APIs: OSRM, OpenRouteService, USGS, IEA
   - Optional demand streaming via REST polling or Kafka

2. **Data Processing & Validation**
   - Pydantic schemas for validation
   - Business rule checks (negative demand, illegal routes)
   - Unit normalization and referential integrity

3. **Optimization Engine**
   - MILP model built with Pyomo
   - Solvers: CBC/HiGHS (default), Gurobi (optional)
   - Decision variables: production, shipments, trips, inventory, mode activation
   - Constraints: capacity, inventory balance, safety stock, batch size

4. **Scenario Engine**
   - Demand scaling scenarios (base/high/low)
   - Stochastic demand draws (normal/triangular)
   - Batch runner for multiple MILP solves
   - KPI calculation: cost, service level, utilization

5. **Visualization & UI**
   - Streamlit app with pages: upload, optimization, KPI, comparison, admin
   - Plotly charts for cost breakdown, utilization, inventory vs safety stock

6. **Integration & Security**
   - FastAPI backend with JWT auth
   - Role-based access: admin, planner, viewer
   - Celery + Redis for async optimization jobs
   - Centralized logging and audit trail

7. **Deployment**
   - Docker Compose: backend, frontend, PostgreSQL, Redis, Celery worker
   - Environment-based configuration via .env and YAML

## Key Design Decisions

- **Pyomo** for MILP to support complex constraints and multiple solvers.
- **Celery + Redis** for long-running optimization tasks.
- **Streamlit** for rapid UI development; can be swapped for React later.
- **Alembic** for database migrations.
- **Loguru** for structured logging (JSON/text).

## Data Flow

1. Upload CSV/Excel → validation → load into PostgreSQL.
2. External routing APIs → cache → enrich transport routes.
3. Demand polling → validate → write to demand_forecast.
4. User selects scenario → Celery job runs MILP → results stored → UI visualizes KPIs.

## Scaling Considerations

- Solver results can be cached per scenario fingerprint.
- Large networks: consider column generation or decomposition.
- Cloud-ready: replace PostgreSQL with RDS, Redis with ElastiCache, and run workers on ECS/Kubernetes.
