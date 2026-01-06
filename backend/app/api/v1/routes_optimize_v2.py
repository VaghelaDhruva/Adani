"""
Optimization API Routes - Production Ready Version

Uses job queue system with SQLite persistence.
No proxy timeout issues - non-blocking endpoints.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import logging
from datetime import datetime
from pydantic import BaseModel

from app.core.deps import get_db
from app.services.job_queue import job_queue_service
from app.services.optimization.pyomo_optimizer import PyomoOptimizer
from app.utils.currency import format_rupees, validate_cost_realism
from app.db.models.optimization_run import OptimizationRun
from app.db.models.job_status import JobStatus

router = APIRouter()
logger = logging.getLogger(__name__)


class OptimizationRequest(BaseModel):
    """Request model for optimization."""
    scenario_name: str
    solver: str = "cbc"  # cbc, highs, gurobi
    time_limit: int = 600
    mip_gap: float = 0.01


def _run_optimization_job(
    db: Session,
    job_id: str,
    scenario_name: str,
    solver: str,
    time_limit: int,
    mip_gap: float
) -> Dict[str, Any]:
    """
    Background job function to run optimization.
    
    This function is called by the job queue service.
    """
    try:
        # Update progress
        job_queue_service.update_job_progress(db, job_id, 20, "Loading input data")
        
        # Load input data from database
        from sqlalchemy import text
        
        # Load plants
        plants_result = db.execute(text("""
            SELECT plant_id, capacity_tonnes, initial_inventory, safety_stock_tonnes, max_storage_tonnes
            FROM plant_master
        """))
        plants = [
            {
                "plant_id": row[0],
                "capacity_tonnes": float(row[1]) if row[1] else 0.0,
                "initial_inventory": float(row[2]) if row[2] else 0.0,
                "safety_stock_tonnes": float(row[3]) if row[3] else 0.0,
                "max_storage_tonnes": float(row[4]) if row[4] else 1000000.0
            }
            for row in plants_result
        ]
        
        # Load customers/GUs
        customers_result = db.execute(text("""
            SELECT customer_id, location
            FROM demand_forecast
            GROUP BY customer_id, location
        """))
        customers = [
            {"customer_id": row[0], "location": row[1]}
            for row in customers_result
        ]
        
        # Load periods
        periods_result = db.execute(text("""
            SELECT DISTINCT period
            FROM demand_forecast
            ORDER BY period
        """))
        periods = [row[0] for row in periods_result]
        
        # Load demand
        demand_result = db.execute(text("""
            SELECT customer_id, period, demand_tonnes
            FROM demand_forecast
        """))
        demand = [
            {
                "customer_id": row[0],
                "period": row[1],
                "demand_tonnes": float(row[2]) if row[2] else 0.0
            }
            for row in demand_result
        ]
        
        # Load routes
        routes_result = db.execute(text("""
            SELECT from_node, to_node, transport_mode, distance_km
            FROM transport_routes_modes
        """))
        routes = [
            {
                "from": row[0],
                "to": row[1],
                "mode": row[2],
                "distance_km": float(row[3]) if row[3] else 0.0
            }
            for row in routes_result
        ]
        
        # Load transport modes
        modes_result = db.execute(text("""
            SELECT DISTINCT transport_mode, vehicle_capacity_tonnes
            FROM transport_routes_modes
        """))
        transport_modes = [
            {
                "mode": row[0],
                "capacity_tonnes": float(row[1]) if row[1] else 30.0
            }
            for row in modes_result
        ]
        
        # Load costs - ALL IN RAW RUPEES
        # Production costs
        prod_cost_result = db.execute(text("""
            SELECT plant_id, period, production_cost_per_tonne
            FROM production_capacity_cost
        """))
        production_costs = {}
        for row in prod_cost_result:
            plant_id = row[0]
            cost = float(row[2]) if row[2] else 1850.0
            if plant_id not in production_costs:
                production_costs[plant_id] = cost  # Use first period's cost as default
        
        # Transport costs
        transport_cost_result = db.execute(text("""
            SELECT from_node, to_node, transport_mode, variable_cost_per_tonne, fixed_cost_per_trip
            FROM transport_routes_modes
        """))
        transport_costs = {}
        fixed_trip_costs = {}
        for row in transport_cost_result:
            route_key = f"{row[0]}_{row[1]}_{row[2]}"
            transport_costs[route_key] = float(row[3]) if row[3] else 250.0
            fixed_trip_costs[route_key] = float(row[4]) if row[4] else 5000.0
        
        # Inventory costs
        holding_cost_result = db.execute(text("""
            SELECT plant_id, holding_cost_per_tonne_period
            FROM plant_master
        """))
        inventory_costs = {}
        for row in holding_cost_result:
            inventory_costs[row[0]] = float(row[1]) if row[1] else 15.0
        
        # Build input data structure
        input_data = {
            "plants": plants,
            "customers": customers,
            "periods": periods,
            "transport_modes": transport_modes,
            "routes": routes,
            "demand": demand,
            "costs": {
                "production": production_costs,
                "transport": transport_costs,
                "fixed_transport": fixed_trip_costs,
                "inventory": inventory_costs,
                "penalty": {"unmet_demand": 10000.0}  # ₹10,000 per ton unmet
            }
        }
        
        job_queue_service.update_job_progress(db, job_id, 40, "Building optimization model")
        
        # Build and solve model
        optimizer = PyomoOptimizer()
        optimizer.build_model(input_data, db)
        
        job_queue_service.update_job_progress(db, job_id, 60, "Solving optimization model")
        
        # Solve
        solve_result = optimizer.solve(
            solver_name=solver,
            time_limit=time_limit,
            mip_gap=mip_gap
        )
        
        job_queue_service.update_job_progress(db, job_id, 80, "Extracting results")
        
        # Extract results
        results = optimizer.extract_results()
        
        # Validate cost realism
        total_cost = results["objective_value"]
        is_valid, warning = validate_cost_realism(total_cost)
        if not is_valid:
            logger.warning(warning)
        
        # Create optimization run record
        optimization_run = OptimizationRun(
            run_id=job_id,
            scenario_name=scenario_name,
            solver_name=solver,
            solver_status=solve_result["solver_status"],
            status="completed",
            objective_value=total_cost,
            solve_time_seconds=solve_result["solve_time"],
            started_at=datetime.now(),  # Will be updated from job status
            completed_at=datetime.now(),
            validation_passed=True
        )
        
        db.add(optimization_run)
        db.commit()
        db.refresh(optimization_run)
        
        # Store detailed results (would go to optimization_results table)
        # For now, store in result_data
        result_data = {
            "objective_value": total_cost,
            "cost_breakdown": results["cost_breakdown"],
            "production_plan_count": len(results["production_plan"]),
            "shipment_plan_count": len(results["shipment_plan"]),
            "warning": warning if not is_valid else None
        }
        
        job_queue_service.update_job_progress(db, job_id, 100, "Optimization completed")
        
        return {
            "result_ref": job_id,
            "result_data": result_data,
            "optimization_run_id": optimization_run.id
        }
        
    except Exception as e:
        logger.error(f"Optimization job {job_id} failed: {e}", exc_info=True)
        raise


@router.post("/optimize")
async def run_optimization(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Run optimization - non-blocking endpoint.
    
    Returns immediately with job_id.
    Client should poll /optimize/{job_id}/status for progress.
    """
    try:
        # Submit job to queue
        job_id = job_queue_service.submit_job(
            db=db,
            job_type="optimization",
            job_function=_run_optimization_job,
            scenario_name=request.scenario_name,
            user_id=None,  # TODO: Get from JWT token
            solver=request.solver,
            time_limit=request.time_limit,
            mip_gap=request.mip_gap
        )
        
        # Add background task
        background_tasks.add_task(
            job_queue_service.execute_job_async,
            db=db,
            job_id=job_id,
            job_function=_run_optimization_job,
            scenario_name=request.scenario_name,
            solver=request.solver,
            time_limit=request.time_limit,
            mip_gap=request.mip_gap
        )
        
        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Optimization job submitted successfully. Poll /optimize/{job_id}/status for progress."
        }
        
    except Exception as e:
        logger.error(f"Error submitting optimization job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit optimization job: {str(e)}")


@router.get("/optimize/{job_id}/status")
async def get_optimization_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get status of optimization job."""
    try:
        status = job_queue_service.get_job_status(db, job_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.get("/optimize/{job_id}/results")
async def get_optimization_results(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed results of completed optimization."""
    try:
        # Get job status
        job_status = job_queue_service.get_job_status(db, job_id)
        if not job_status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        if job_status["status"] not in ["success", "failed"]:
            raise HTTPException(
                status_code=202,
                detail=f"Job {job_id} is still {job_status['status']}. Status: {job_status.get('progress_message', '')}"
            )
        
        if job_status["status"] == "failed":
            raise HTTPException(
                status_code=500,
                detail=f"Optimization failed: {job_status.get('error', 'Unknown error')}"
            )
        
        # Load optimization run
        optimization_run = db.query(OptimizationRun).filter(
            OptimizationRun.run_id == job_id
        ).first()
        
        if not optimization_run:
            raise HTTPException(status_code=404, detail="Optimization run not found")
        
        # Load detailed results from optimizer (would be stored in optimization_results table)
        # For now, return summary
        return {
            "job_id": job_id,
            "scenario_name": job_status["scenario_name"],
            "status": "completed",
            "objective_value": optimization_run.objective_value,
            "objective_value_formatted": format_rupees(optimization_run.objective_value),
            "solve_time": optimization_run.solve_time_seconds,
            "solver_status": optimization_run.solver_status,
            "result_ref": job_status.get("result_ref"),
            "result_data": job_status.get("result_data", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting optimization results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get optimization results: {str(e)}")


@router.post("/optimize/{job_id}/cancel")
async def cancel_optimization(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Cancel a pending or running optimization job."""
    try:
        success = job_queue_service.cancel_job(db, job_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Cannot cancel job {job_id}. It may already be completed or failed.")
        
        return {
            "job_id": job_id,
            "status": "cancelled",
            "message": "Job cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")

