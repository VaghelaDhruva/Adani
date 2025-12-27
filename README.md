# Clinker Supply Chain Optimization System

Production-grade system for real-time and batch data ingestion, MILP optimization, scenario simulation, and visualization dashboards for clinker logistics.

## Architecture

- **Backend**: FastAPI + SQLAlchemy + Pydantic + Celery + Redis
- **DB**: PostgreSQL
- **Optimization**: Pyomo (CBC/HiGHS default; Gurobi optional)
- **Frontend**: Streamlit
- **Auth**: JWT with role-based access (admin, planner, viewer)
- **Infra**: Docker Compose (backend, frontend, postgres, worker, redis)

## Quick Start

```bash
# Copy environment file and configure
cp infra/env.example .env
# Edit .env with your DB, routing, and auth settings

# Start services
docker-compose -f infra/docker-compose.yml up --build -d

# Run migrations
docker-compose -f infra/docker-compose.yml exec backend alembic upgrade head

# Access
# - Streamlit UI: http://localhost:8501
# - FastAPI docs: http://localhost:8000/docs
# - API health: http://localhost:8000/health
```

## Project Structure

See `docs/architecture.md` for detailed module breakdown.

## Data Ingestion

- CSV/Excel upload via API
- External routing APIs (OSRM, OpenRouteService) with caching
- Optional demand streaming via REST polling or Kafka (scaffolded)

## Optimization

- MILP model with production, transport, inventory, and batch constraints
- Scenario engine for demand uncertainty and batch runs
- KPI calculation and visualization

## Development

```bash
# Backend dev
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend dev
cd frontend/streamlit_app
pip install -r requirements.txt
streamlit run main.py --server.port 8501
```

## Testing

```bash
cd backend
pytest
```

## License

Internal use.
