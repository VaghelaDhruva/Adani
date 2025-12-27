# API Contracts (FastAPI)

## Base URL
`http://localhost:8000/api/v1`

## Authentication
- Bearer token (JWT) obtained via `/auth/login`.
- Roles: admin, planner, viewer.

## Endpoints

### Health
- `GET /health` – status check.

### Auth
- `POST /auth/login` – login (OAuth2PasswordRequestForm).
- `GET /auth/me` – current user info.

### Data Management
- `POST /data/plants/` – create plant.
- `GET /data/plants/` – list plants.
- `POST /data/demand/` – create demand forecast.
- `GET /data/demand/` – list demand.
- `POST /data/transport_routes/` – create transport route.
- `GET /data/transport_routes/` – list routes.
- `POST /data/safety_stock/` – create safety stock policy.
- `GET /data/safety_stock/` – list policies.
- `POST /data/initial_inventory/` – create initial inventory.
- `GET /data/initial_inventory/` – list inventory.
- `POST /data/upload_csv` – generic CSV upload (multipart).

### Scenarios
- `POST /scenarios/` – create scenario.
- `GET /scenarios/` – list scenarios.
- `GET /scenarios/{scenario_name}` – get scenario.
- `PUT /scenarios/{scenario_name}` – update scenario.
- `DELETE /scenarios/{scenario_name}` – delete scenario.

### Optimization
- `POST /optimization/run` – trigger optimization for a scenario (returns job_id).
- `GET /optimization/status/{job_id}` – check job status.
- `GET /optimization/result/{scenario_name}` – fetch latest result.

### KPIs
- `GET /kpi/dashboard/{scenario_name}` – KPI dashboard for a scenario.
- `POST /kpi/compare` – compare KPIs across multiple scenarios (JSON list of names).

## Request/Response Shapes

See `schemas/` for Pydantic models. Examples:

- PlantMasterCreate: `{plant_id, plant_name, plant_type, latitude?, longitude?, region?, country?}`
- DemandForecastCreate: `{customer_node_id, period, demand_tonnes, demand_low_tonnes?, demand_high_tonnes?, confidence_level?, source?}`
- ScenarioMetadataCreate: `{scenario_name, description?, demand_multiplier?, transport_cost_multiplier?, production_cost_multiplier?, solver?, time_limit_seconds?, mip_gap?, status?, created_by?}`

## Errors

Standard HTTP status codes with JSON body:
```json
{"detail": "error message"}
```
