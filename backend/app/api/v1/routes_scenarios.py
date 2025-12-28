from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

import pandas as pd

from app.core.deps import get_db
from app.db.models import (
    PlantMaster,
    ProductionCapacityCost,
    TransportRoutesModes,
    DemandForecast,
    SafetyStockPolicy,
    InitialInventory,
)
from app.schemas.scenario import ScenarioMetadata, ScenarioMetadataCreate, ScenarioMetadataUpdate
from app.services.scenarios.scenario_generator import ScenarioConfig
from app.services.scenarios.scenario_runner import run_batch_scenarios_from_configs
from app.services.audit_service import audit_timer
from app.utils.exceptions import DataValidationError, OptimizationError


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=ScenarioMetadata)
def create_scenario(scenario: ScenarioMetadataCreate, db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/", response_model=List[ScenarioMetadata])
def list_scenarios(db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{scenario_name}", response_model=ScenarioMetadata)
def get_scenario(scenario_name: str, db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("/{scenario_name}", response_model=ScenarioMetadata)
def update_scenario(scenario_name: str, scenario: ScenarioMetadataUpdate, db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/{scenario_name}")
def delete_scenario(scenario_name: str, db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


def _load_optimization_data(db: Session) -> Dict[str, pd.DataFrame]:
	"""Load cleaned DataFrames required by the optimization engine from the DB.

	This is a thin data-access helper; business logic remains in services.
	"""

	plants = pd.DataFrame([
		{
			"plant_id": p.plant_id,
			"plant_name": p.plant_name,
			"plant_type": p.plant_type,
			"latitude": p.latitude,
			"longitude": p.longitude,
			"region": p.region,
			"country": p.country,
		}
		for p in db.query(PlantMaster).all()
	])

	prod = pd.DataFrame([
		{
			"plant_id": r.plant_id,
			"period": r.period,
			"max_capacity_tonnes": r.max_capacity_tonnes,
			"variable_cost_per_tonne": r.variable_cost_per_tonne,
			"holding_cost_per_tonne": r.holding_cost_per_tonne,
		}
		for r in db.query(ProductionCapacityCost).all()
	])

	routes = pd.DataFrame([
		{
			"origin_plant_id": r.origin_plant_id,
			"destination_node_id": r.destination_node_id,
			"transport_mode": r.transport_mode,
			"distance_km": r.distance_km,
			"cost_per_tonne": r.cost_per_tonne,
			"cost_per_tonne_km": r.cost_per_tonne_km,
			"fixed_cost_per_trip": r.fixed_cost_per_trip,
			"vehicle_capacity_tonnes": r.vehicle_capacity_tonnes,
			"min_batch_quantity_tonnes": r.min_batch_quantity_tonnes,
		}
		for r in db.query(TransportRoutesModes).all()
	])

	demand = pd.DataFrame([
		{
			"customer_node_id": d.customer_node_id,
			"period": d.period,
			"demand_tonnes": d.demand_tonnes,
		}
		for d in db.query(DemandForecast).all()
	])

	safety_stock = pd.DataFrame([
		{
			"node_id": s.node_id,
			"policy_type": s.policy_type,
			"policy_value": s.policy_value,
			"safety_stock_tonnes": s.safety_stock_tonnes,
			"max_inventory_tonnes": s.max_inventory_tonnes,
		}
		for s in db.query(SafetyStockPolicy).all()
	])

	initial_inventory = pd.DataFrame([
		{
			"node_id": inv.node_id,
			"period": inv.period,
			"inventory_tonnes": inv.inventory_tonnes,
		}
		for inv in db.query(InitialInventory).all()
	])

	# Derive time periods from demand if not explicitly configured
	time_periods = sorted(demand["period"].unique().tolist()) if not demand.empty else []

	return {
		"plants": plants,
		"production_capacity_cost": prod,
		"transport_routes_modes": routes,
		"demand_forecast": demand,
		"safety_stock_policy": safety_stock,
		"initial_inventory": initial_inventory,
		"time_periods": time_periods,
	}


@router.post("/run")
def run_scenarios(
	scenarios: List[ScenarioConfig],
	db: Session = Depends(get_db),
):
	"""Run one or more optimization scenarios based on ScenarioConfig list.

	This is a thin API wrapper that:
	- validates the request body via ScenarioConfig
	- loads cleaned DataFrames from the database
	- delegates execution to the scenario runner
	"""

	user = "system"  # TODO: get from auth when available
	metadata = {"scenario_count": len(scenarios), "scenario_names": [s.name for s in scenarios]}

	with audit_timer(user, "run_scenarios", db, metadata) as timer:
		try:
			data = _load_optimization_data(db)
			if data["demand_forecast"].empty:
				raise DataValidationError("No demand data available for scenarios")
			result = run_batch_scenarios_from_configs(data, scenarios)
			timer.set_success()
			return result
		except DataValidationError as e:
			logger.error("Scenario run validation error: %s", e)
			timer.set_failure(str(e))
			raise HTTPException(status_code=400, detail=str(e))
		except OptimizationError as e:
			logger.error("Scenario run optimization error: %s", e)
			timer.set_failure(str(e))
			raise HTTPException(status_code=400, detail=str(e))
		except HTTPException:
			# Re-raise explicit HTTP errors unchanged
			raise
		except Exception as e:
			logger.exception("Unexpected error while running scenarios")
			timer.set_failure("Unexpected error")
			raise HTTPException(status_code=500, detail="Failed to run scenarios") from None
