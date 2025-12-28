# DATA LAYER DOCUMENTATION

## 1) DATA SOURCES

### Database Tables / ORM Models

| Table (ORM Model) | Module | Key Fields Used by Optimizer |
|-------------------|--------|------------------------------|
| `PlantMaster` | `app.db.models.plant_master.PlantMaster` | `plant_id`, `plant_name`, `plant_type`, `latitude`, `longitude`, `region`, `country` |
| `ProductionCapacityCost` | `app.db.models.production_capacity_cost.ProductionCapacityCost` | `plant_id`, `period`, `max_capacity_tonnes`, `variable_cost_per_tonne`, `holding_cost_per_tonne` |
| `TransportRoutesModes` | `app.db.models.transport_routes_modes.TransportRoutesModes` | `origin_plant_id`, `destination_node_id`, `transport_mode`, `distance_km`, `cost_per_tonne`, `cost_per_tonne_km`, `fixed_cost_per_trip`, `vehicle_capacity_tonnes`, `min_batch_quantity_tonnes` |
| `DemandForecast` | `app.db.models.demand_forecast.DemandForecast` | `customer_node_id`, `period`, `demand_tonnes` |
| `SafetyStockPolicy` | `app.db.models.safety_stock_policy.SafetyStockPolicy` | `node_id`, `policy_type`, `policy_value`, `safety_stock_tonnes`, `max_inventory_tonnes` |
| `InitialInventory` | `app.db.models.initial_inventory.InitialInventory` | `node_id`, `period`, `inventory_tonnes` |

### Data Loading Functions

- **Function**: `_load_optimization_data(db: Session)`
- **Location**: `app.api.v1.routes_scenarios.py`
- **Purpose**: Queries each ORM model and builds a `Dict[str, pd.DataFrame]` for the optimizer/scenario engine.
- **Returns**:
  ```python
  {
      "plants": DataFrame([...]),
      "production_capacity_cost": DataFrame([...]),
      "transport_routes_modes": DataFrame([...]),
      "demand_forecast": DataFrame([...]),
      "safety_stock_policy": DataFrame([...]),
      "initial_inventory": DataFrame([...]),
      "time_periods": List[str],
  }
  ```

---

## 2) DATAFLOW

```
[Database Tables]
      |
      v
[SQLAlchemy ORM Models]
      |
      v
_load_optimization_data(db)  -->  Dict[str, pd.DataFrame]
      |
      v
[Scenario Engine]
      |-- generate_demand_for_scenario (scales/stochasticizes demand)
      |-- build_clinker_model (MILP construction)
      |-- solve_model (solver execution)
      |-- extract_solution (structured results)
      |-- compute_kpis (metrics)
      |
      v
[JSON API Response]  <--  POST /api/v1/scenarios/run
```

- **Validation**:
  - API layer checks `demand_forecast` is non-empty.
  - Scenario generator validates `ScenarioConfig` via Pydantic.
  - Model builder uses `_safe_float` to coerce missing numeric values to 0.0.
  - Solver wrapper checks solver status/termination and raises `OptimizationError` on failure.

---

## 3) TIME PERIODS

- **Determination**:
  ```python
  time_periods = sorted(demand["period"].unique().tolist()) if not demand.empty else []
  ```
- **Location**: `_load_optimization_data`
- **Fallback**: If `demand_forecast` is empty, `time_periods` is `[]`.
- **Usage**:
  - MILP builder uses this list if provided; otherwise derives from `demand_df["period"].unique()` again.
  - Scenario generation does **not** alter periods; it only scales demand within existing periods.

---

## 4) REQUIRED vs OPTIONAL FIELDS

| Table / Model | Required for MILP | Optional (defaulted) | Effect if Missing |
|---------------|-------------------|---------------------|-------------------|
| `PlantMaster` | `plant_id` | all others | Empty plant set → MILP trivial/infeasible |
| `ProductionCapacityCost` | `plant_id`, `period`, `max_capacity_tonnes`, `variable_cost_per_tonne` | `holding_cost_per_tonne` | Missing capacity/cost → unbounded or zero production |
| `TransportRoutesModes` | `origin_plant_id`, `destination_node_id`, `transport_mode` | cost/capacity/batch columns | No routes → demand cannot be satisfied → infeasible |
| `DemandForecast` | `customer_node_id`, `period`, `demand_tonnes` | none | Empty demand → API returns 400 early |
| `SafetyStockPolicy` | none | all | No safety stock constraints |
| `InitialInventory` | none | all | `inv0` defaults to 0.0 per plant |

### Exceptions Raised

- **API layer** (`routes_scenarios.py`):
  - `DataValidationError` → HTTP 400 if `demand_forecast` is empty.
  - Generic `Exception` → HTTP 500 with generic message.
- **Scenario generatorDecoration generator**gens** (`scenario_generator.py`):
  - `OptimizationError` for unsupported scenario types or distribution parameters.
- **Solver wrapper** (`solvers.py`):
  - `OptimizationError` if solver status is not ok/feasible/optimal.
- **Scenario runner** (`scenario_runner.py`):
  - Catches `OptimizationError` and returns a JSON error payload instead of raising.

---

## 5) REAL-TIME vs SYNTHETIC DATA

- **Current implementation**: Data is sourced from **database tables** via SQLAlchemy ORM models.
- **Real-time ingestion**: Not active in the current codebase.
- **Scaffolds for external feeds**:
  - `app.services.ingestion.*` modules exist (CSV, Excel, PDF, IEA, USGS, company reports) but are **not wired into the MILP/scenario flow**.
  - `app.services.external.*` includes `ors_client.py` and `osrm_client.py` for routing, but the optimizer uses static `distance_km` from `TransportRoutesModes`.
  - `app.services.job_queue.py` and Celery are present but not used in the scenario execution path.
- **Conclusion**: The system operates on **static, pre-loaded data** from the DB; real-time or streaming ingestion is scaffolded but not integrated.

---

## 6) CACHING / PERFORMANCE NOTES

- No explicit caching layer is implemented in the current data loading path.
- `_load_optimization_data` materializes entire tables into pandas DataFrames; for very large datasets this may be memory-intensive.
- No lazy loading or pagination is used; each request to `/api/v1/scenarios/run` loads the full dataset.

---

## 7) RISKS / EDGE CASES

- **Missing demand**: API returns 400 early; optimization never runs.
- **Empty plants/routes/capacity**: MILP may be infeasible; solver will raise `OptimizationError`.
- **Mismatched IDs**: If `plant_id` values in production/capacity do not exist in `plants`, those rows are silently ignored (sets derived from `plants` and `demand` only).
- **Nulls in numeric columns**: `_safe_float` converts to 0.0, potentially masking data quality issues.
- **Duplicate periods**: Loader deduplicates via `.unique()`; duplicates are collapsed.
- **Invalid routes**: `reject_illegal_routes` in `validation/rules.py` checks `origin == destination` but is not called automatically in the current flow.
- **Unit consistency**: `normalize_cost_units` and `enforce_unit_consistency` are placeholders; no active enforcement.
- **Large datasets**: Full-table loads may cause memory pressure; no streaming or pagination.
- **Scenario scaling**: Scaling factors can produce demand that exceeds capacity, leading to infeasible scenarios; reported as failed scenarios.
