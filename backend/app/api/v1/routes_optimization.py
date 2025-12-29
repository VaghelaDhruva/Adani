"""
Optimization Engine API Routes

Provides endpoints for running the actual mathematical optimization engine
and retrieving optimization results with detailed solution data.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta
import json
import asyncio
from pydantic import BaseModel

from app.core.deps import get_db
from app.services.optimization.optimization_engine import optimization_engine, create_sample_input_data
from app.utils.exceptions import OptimizationError, DataValidationError

router = APIRouter()
logger = logging.getLogger(__name__)

# Store running optimizations
running_optimizations = {}
completed_optimizations = {}


class OptimizationRequest(BaseModel):
    """Request model for optimization."""
    scenario_name: str = "base"
    solver: str = "PULP_CBC_CMD"
    time_limit: int = 600
    mip_gap: float = 0.01
    use_sample_data: bool = True
    input_data: Optional[Dict[str, Any]] = None


class OptimizationStatus(BaseModel):
    """Status model for optimization."""
    run_id: str
    status: str
    progress: int
    start_time: str
    estimated_completion: Optional[str] = None
    error_message: Optional[str] = None


@router.post("/optimize")
async def run_optimization(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Run mathematical optimization with the actual optimization engine."""
    try:
        # Generate unique run ID
        run_id = f"OPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize optimization status
        running_optimizations[run_id] = {
            "status": "initializing",
            "progress": 0,
            "start_time": datetime.now().isoformat(),
            "scenario_name": request.scenario_name,
            "solver": request.solver,
            "time_limit": request.time_limit
        }
        
        # Run optimization in background
        background_tasks.add_task(
            _run_optimization_task,
            run_id,
            request
        )
        
        return {
            "run_id": run_id,
            "status": "queued",
            "message": "Optimization started successfully",
            "estimated_runtime": f"{request.time_limit} seconds (max)",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting optimization: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start optimization: {str(e)}")


async def _run_optimization_task(run_id: str, request: OptimizationRequest):
    """Background task to run the optimization."""
    try:
        # Update status to building model
        running_optimizations[run_id]["status"] = "building_model"
        running_optimizations[run_id]["progress"] = 10
        
        # Get input data
        if request.use_sample_data or not request.input_data:
            input_data = create_sample_input_data()
            # Modify based on scenario
            input_data = _modify_data_for_scenario(input_data, request.scenario_name)
        else:
            input_data = request.input_data
        
        # Build optimization model
        optimization_engine.build_model(input_data)
        
        # Update status to solving
        running_optimizations[run_id]["status"] = "solving"
        running_optimizations[run_id]["progress"] = 30
        
        # Solve the model
        result = optimization_engine.solve(
            solver_name=request.solver,
            time_limit=request.time_limit
        )
        
        # Update status to processing results
        running_optimizations[run_id]["status"] = "processing_results"
        running_optimizations[run_id]["progress"] = 90
        
        # Get model statistics
        model_stats = optimization_engine.get_model_statistics()
        
        # Prepare final result
        final_result = {
            "run_id": run_id,
            "scenario_name": request.scenario_name,
            "solver": request.solver,
            "time_limit": request.time_limit,
            "model_statistics": model_stats,
            "optimization_result": result,
            "input_data_summary": {
                "plants_count": len(input_data.get("plants", [])),
                "customers_count": len(input_data.get("customers", [])),
                "periods_count": len(input_data.get("periods", [])),
                "routes_count": len(input_data.get("routes", [])),
                "total_demand": sum(d["demand_tonnes"] for d in input_data.get("demand", []))
            },
            "completion_time": datetime.now().isoformat()
        }
        
        # Move to completed optimizations
        completed_optimizations[run_id] = final_result
        
        # Update final status
        running_optimizations[run_id]["status"] = "completed"
        running_optimizations[run_id]["progress"] = 100
        
        logger.info(f"Optimization {run_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Optimization {run_id} failed: {e}")
        
        # Update error status
        running_optimizations[run_id]["status"] = "failed"
        running_optimizations[run_id]["error_message"] = str(e)
        running_optimizations[run_id]["progress"] = 0


def _modify_data_for_scenario(input_data: Dict[str, Any], scenario_name: str) -> Dict[str, Any]:
    """Modify input data based on scenario."""
    
    if scenario_name == "high_demand":
        # Increase demand by 25%
        for demand_record in input_data["demand"]:
            demand_record["demand_tonnes"] = int(demand_record["demand_tonnes"] * 1.25)
    
    elif scenario_name == "low_demand":
        # Decrease demand by 20%
        for demand_record in input_data["demand"]:
            demand_record["demand_tonnes"] = int(demand_record["demand_tonnes"] * 0.8)
    
    elif scenario_name == "capacity_constrained":
        # Reduce plant capacities by 15%
        for plant in input_data["plants"]:
            plant["capacity_tonnes"] = int(plant["capacity_tonnes"] * 0.85)
    
    elif scenario_name == "transport_disruption":
        # Increase transport costs by 40%
        for route_key in input_data["costs"]["transport"]:
            input_data["costs"]["transport"][route_key] = int(
                input_data["costs"]["transport"][route_key] * 1.4
            )
    
    elif scenario_name == "fuel_price_spike":
        # Increase all transport costs by 30%
        for route_key in input_data["costs"]["transport"]:
            input_data["costs"]["transport"][route_key] = int(
                input_data["costs"]["transport"][route_key] * 1.3
            )
        for route_key in input_data["costs"]["fixed_transport"]:
            input_data["costs"]["fixed_transport"][route_key] = int(
                input_data["costs"]["fixed_transport"][route_key] * 1.3
            )
    
    return input_data


@router.get("/optimize/{run_id}/status")
async def get_optimization_status(run_id: str):
    """Get status of a running or completed optimization."""
    try:
        if run_id in running_optimizations:
            status_data = running_optimizations[run_id]
            
            # Calculate estimated completion if still running
            estimated_completion = None
            if status_data["status"] in ["building_model", "solving", "processing_results"]:
                start_time = datetime.fromisoformat(status_data["start_time"])
                estimated_duration = status_data.get("time_limit", 600)
                estimated_completion = (start_time + timedelta(seconds=estimated_duration)).isoformat()
            
            return OptimizationStatus(
                run_id=run_id,
                status=status_data["status"],
                progress=status_data["progress"],
                start_time=status_data["start_time"],
                estimated_completion=estimated_completion,
                error_message=status_data.get("error_message")
            )
        
        elif run_id in completed_optimizations:
            return OptimizationStatus(
                run_id=run_id,
                status="completed",
                progress=100,
                start_time=completed_optimizations[run_id]["optimization_result"]["timestamp"],
                estimated_completion=None,
                error_message=None
            )
        
        else:
            raise HTTPException(status_code=404, detail="Optimization run not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting optimization status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get optimization status: {str(e)}")


@router.get("/optimize/{run_id}/results")
async def get_optimization_results(run_id: str):
    """Get detailed results of a completed optimization."""
    try:
        if run_id not in completed_optimizations:
            if run_id in running_optimizations:
                status = running_optimizations[run_id]["status"]
                if status == "failed":
                    error_msg = running_optimizations[run_id].get("error_message", "Unknown error")
                    raise HTTPException(status_code=500, detail=f"Optimization failed: {error_msg}")
                else:
                    raise HTTPException(status_code=202, detail="Optimization still running")
            else:
                raise HTTPException(status_code=404, detail="Optimization run not found")
        
        result = completed_optimizations[run_id]
        
        # Transform result to match the expected API format
        opt_result = result["optimization_result"]
        solution = opt_result["solution"]
        
        # Calculate service level
        total_demand = result["input_data_summary"]["total_demand"]
        unmet_demand = sum(item["tonnes"] for item in solution.get("unmet_demand", []))
        service_level = max(0, (total_demand - unmet_demand) / total_demand) if total_demand > 0 else 1.0
        
        # Calculate capacity utilization
        capacity_utilization = {}
        for prod_item in solution.get("production", []):
            plant_id = prod_item["plant_id"]
            if plant_id not in capacity_utilization:
                capacity_utilization[plant_id] = 0
            capacity_utilization[plant_id] += prod_item["tonnes"]
        
        # Normalize by capacity (this would need actual capacity data)
        for plant_id in capacity_utilization:
            capacity_utilization[plant_id] = min(1.0, capacity_utilization[plant_id] / 100000)  # Assuming 100k capacity
        
        # Format response to match expected API contract
        formatted_result = {
            "run_id": run_id,
            "timestamp": result["completion_time"],
            "solver_status": opt_result["status"],
            "runtime_seconds": opt_result["runtime_seconds"],
            "optimality_gap": opt_result.get("optimality_gap"),
            
            # Cost breakdown
            "total_cost": opt_result["objective_value"],
            "production_cost": opt_result["objective_components"]["production_cost"],
            "transportation_cost": opt_result["objective_components"]["transport_cost"],
            "fixed_trip_cost": opt_result["objective_components"]["fixed_transport_cost"],
            "holding_cost": opt_result["objective_components"]["inventory_cost"],
            "penalty_cost": opt_result["objective_components"]["penalty_cost"],
            
            # Performance metrics
            "service_level": service_level,
            "capacity_utilization": capacity_utilization,
            "avg_utilization": sum(capacity_utilization.values()) / len(capacity_utilization) if capacity_utilization else 0,
            
            # Detailed solution
            "production": solution.get("production", []),
            "shipments": solution.get("transport", []),
            "inventory": solution.get("inventory", []),
            "unmet_demand": solution.get("unmet_demand", []),
            
            # Additional metrics
            "stockout_risk": unmet_demand / total_demand if total_demand > 0 else 0,
            "total_production": sum(p["tonnes"] for p in solution.get("production", [])),
            "total_shipments": sum(s["tonnes"] for s in solution.get("transport", [])),
            "total_inventory": sum(i["tonnes"] for i in solution.get("inventory", [])),
            
            # Model and solver details
            "solver": result["solver"],
            "model_statistics": result["model_statistics"],
            "scenario_name": result["scenario_name"],
            "termination_reason": opt_result.get("termination_reason", opt_result["status"])
        }
        
        return formatted_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting optimization results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get optimization results: {str(e)}")


@router.get("/optimize/runs")
async def get_optimization_runs(
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None)
):
    """Get list of optimization runs."""
    try:
        runs = []
        
        # Add completed runs
        for run_id, result in completed_optimizations.items():
            opt_result = result["optimization_result"]
            runs.append({
                "run_id": run_id,
                "status": "completed",
                "timestamp": result["completion_time"],
                "scenario": result["scenario_name"],
                "solver": result["solver"],
                "runtime_seconds": opt_result["runtime_seconds"],
                "total_cost": opt_result["objective_value"],
                "solver_status": opt_result["status"]
            })
        
        # Add running runs
        for run_id, status_data in running_optimizations.items():
            if run_id not in completed_optimizations:  # Avoid duplicates
                runs.append({
                    "run_id": run_id,
                    "status": status_data["status"],
                    "timestamp": status_data["start_time"],
                    "scenario": status_data["scenario_name"],
                    "solver": status_data["solver"],
                    "runtime_seconds": None,
                    "total_cost": None,
                    "solver_status": None
                })
        
        # Apply status filter
        if status_filter:
            runs = [run for run in runs if run["status"] == status_filter]
        
        # Sort by timestamp (newest first) and limit
        runs.sort(key=lambda x: x["timestamp"], reverse=True)
        runs = runs[:limit]
        
        return {
            "runs": runs,
            "total_count": len(runs),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting optimization runs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get optimization runs: {str(e)}")


@router.delete("/optimize/{run_id}")
async def delete_optimization_run(run_id: str):
    """Delete an optimization run and its results."""
    try:
        deleted = False
        
        if run_id in completed_optimizations:
            del completed_optimizations[run_id]
            deleted = True
        
        if run_id in running_optimizations:
            del running_optimizations[run_id]
            deleted = True
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Optimization run not found")
        
        return {
            "message": f"Optimization run {run_id} deleted successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting optimization run: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete optimization run: {str(e)}")


@router.get("/optimize/scenarios")
async def get_available_scenarios():
    """Get list of available optimization scenarios."""
    return {
        "scenarios": [
            {
                "name": "base",
                "description": "Base case scenario with current demand and capacity",
                "modifications": "None"
            },
            {
                "name": "high_demand",
                "description": "High demand scenario (+25% demand)",
                "modifications": "Demand increased by 25%"
            },
            {
                "name": "low_demand",
                "description": "Low demand scenario (-20% demand)",
                "modifications": "Demand decreased by 20%"
            },
            {
                "name": "capacity_constrained",
                "description": "Capacity constrained scenario (-15% capacity)",
                "modifications": "Plant capacities reduced by 15%"
            },
            {
                "name": "transport_disruption",
                "description": "Transport disruption scenario (+40% transport costs)",
                "modifications": "Transport costs increased by 40%"
            },
            {
                "name": "fuel_price_spike",
                "description": "Fuel price spike scenario (+30% transport costs)",
                "modifications": "All transport costs increased by 30%"
            }
        ],
        "timestamp": datetime.now().isoformat()
    }


@router.get("/optimize/solvers")
async def get_available_solvers():
    """Get list of available optimization solvers."""
    return {
        "solvers": [
            {
                "name": "PULP_CBC_CMD",
                "description": "CBC (Coin-or Branch and Cut) - Open source MILP solver",
                "type": "MILP",
                "license": "Open Source",
                "recommended": True
            },
            {
                "name": "HIGHS",
                "description": "HiGHS - High performance optimization solver",
                "type": "LP/MILP",
                "license": "Open Source",
                "recommended": True
            },
            {
                "name": "GUROBI",
                "description": "Gurobi - Commercial optimization solver",
                "type": "LP/MILP/QP",
                "license": "Commercial",
                "recommended": False,
                "note": "Requires license"
            }
        ],
        "default_solver": "PULP_CBC_CMD",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/optimize/model-template")
async def get_model_template():
    """Get template for optimization input data."""
    template = create_sample_input_data()
    
    return {
        "template": template,
        "description": "Template structure for optimization input data",
        "required_fields": [
            "plants", "customers", "periods", "transport_modes", 
            "routes", "demand", "costs"
        ],
        "timestamp": datetime.now().isoformat()
    }


@router.post("/optimize/validate-input")
async def validate_optimization_input(input_data: Dict[str, Any]):
    """Validate optimization input data."""
    try:
        # Use the optimization engine's validation
        optimization_engine._validate_input_data(input_data)
        
        return {
            "valid": True,
            "message": "Input data validation passed",
            "summary": {
                "plants_count": len(input_data.get("plants", [])),
                "customers_count": len(input_data.get("customers", [])),
                "periods_count": len(input_data.get("periods", [])),
                "routes_count": len(input_data.get("routes", [])),
                "total_demand": sum(d["demand_tonnes"] for d in input_data.get("demand", []))
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except (DataValidationError, OptimizationError) as e:
        return {
            "valid": False,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error validating input data: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")