from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
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
from app.services.scenario_crud_service import scenario_service
from app.services.crud_service import create_standardized_response, create_paginated_response
from app.services.audit_service import audit_timer
from app.utils.exceptions import DataValidationError, OptimizationError


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=Dict[str, Any])
def create_scenario(scenario: ScenarioMetadataCreate, db: Session = Depends(get_db)):
    """
    PHASE 3: Create a new scenario metadata record.
    
    Creates scenario metadata for tracking optimization scenarios.
    Validates input and ensures unique scenario names.
    """
    try:
        new_scenario = scenario_service.create_scenario(scenario)
        return create_standardized_response(
            data=new_scenario.dict(),
            message=f"Created scenario '{scenario.name}'",
            status_code=201
        )
    except DataValidationError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating scenario: {e}")
        raise HTTPException(status_code=500, detail="Failed to create scenario")


@router.get("/", response_model=Dict[str, Any])
def list_scenarios(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    created_by: Optional[str] = Query(None, description="Filter by creator"),
    db: Session = Depends(get_db)
):
    """
    PHASE 3: List scenarios with pagination and filtering.
    
    Returns paginated list of scenario metadata with optional filtering
    by status and creator.
    """
    try:
        result = scenario_service.list_scenarios(
            skip=skip, 
            limit=limit,
            status_filter=status,
            created_by_filter=created_by
        )
        
        return create_paginated_response(
            items=[item.dict() for item in result["items"]],
            total=result["total"],
            skip=result["skip"],
            limit=result["limit"],
            has_next=result["has_next"],
            has_prev=result["has_prev"],
            message=f"Retrieved {len(result['items'])} scenarios"
        )
    except DataValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing scenarios: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve scenarios")


@router.get("/{scenario_name}", response_model=Dict[str, Any])
def get_scenario(scenario_name: str, db: Session = Depends(get_db)):
    """
    PHASE 3: Get a specific scenario by name.
    
    Returns detailed scenario metadata including parameters and status.
    """
    try:
        scenario = scenario_service.get_scenario(scenario_name)
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        return create_standardized_response(
            data=scenario.dict(),
            message=f"Retrieved scenario '{scenario_name}'"
        )
    except HTTPException:
        raise
    except DataValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting scenario {scenario_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve scenario")


@router.put("/{scenario_name}", response_model=Dict[str, Any])
def update_scenario(
    scenario_name: str, 
    scenario: ScenarioMetadataUpdate, 
    db: Session = Depends(get_db)
):
    """
    PHASE 3: Update an existing scenario.
    
    Updates scenario metadata. Name cannot be changed after creation.
    """
    try:
        updated_scenario = scenario_service.update_scenario(scenario_name, scenario)
        if not updated_scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        return create_standardized_response(
            data=updated_scenario.dict(),
            message=f"Updated scenario '{scenario_name}'"
        )
    except HTTPException:
        raise
    except DataValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating scenario {scenario_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update scenario")


@router.delete("/{scenario_name}", response_model=Dict[str, Any])
def delete_scenario(scenario_name: str, db: Session = Depends(get_db)):
    """
    PHASE 3: Delete a scenario by name.
    
    Permanently removes scenario metadata. This action cannot be undone.
    """
    try:
        deleted = scenario_service.delete_scenario(scenario_name)
        if not deleted:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        return create_standardized_response(
            data={"scenario_name": scenario_name, "deleted": True},
            message=f"Deleted scenario '{scenario_name}'"
        )
    except HTTPException:
        raise
    except DataValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting scenario {scenario_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete scenario")


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
	"""
	PHASE 6: Run optimization scenarios with proper user context.
	
	Executes scenario optimization with audit logging and user tracking.
	User context will be integrated when authentication system is implemented.
	
	Run one or more optimization scenarios based on ScenarioConfig list.

	This is a thin API wrapper that:
	- validates the request body via ScenarioConfig
	- loads cleaned DataFrames from the database
	- delegates execution to the scenario runner
	"""

	user = "system"  # PHASE 6: Will be replaced with real user from auth context
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
