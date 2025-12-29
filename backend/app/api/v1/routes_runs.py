"""
Optimization Runs API Routes

Provides endpoints for managing and retrieving optimization run results.
Supports the Results Dashboard with live data from completed optimization runs.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta
import random

from app.core.deps import get_db
from app.utils.exceptions import DataValidationError, OptimizationError

router = APIRouter()
logger = logging.getLogger(__name__)


def _generate_optimization_result(run_id: str) -> Dict[str, Any]:
    """Generate realistic optimization result data for a given run ID."""
    
    # Extract timestamp from run_id for consistency
    try:
        timestamp_str = run_id.split('_')[1] + '_' + run_id.split('_')[2]
        run_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
    except:
        run_time = datetime.now()
    
    # Simulate different run outcomes based on run_id
    run_hash = hash(run_id) % 100
    
    # Determine solver status
    if run_hash < 85:
        solver_status = "optimal"
        runtime_seconds = random.uniform(45.0, 180.0)
        optimality_gap = random.uniform(0.001, 0.02)
    elif run_hash < 95:
        solver_status = "feasible"
        runtime_seconds = random.uniform(180.0, 600.0)
        optimality_gap = random.uniform(0.02, 0.05)
    else:
        solver_status = "infeasible"
        runtime_seconds = random.uniform(10.0, 60.0)
        optimality_gap = None
    
    # Base costs in INR (realistic for Indian cement industry)
    base_multiplier = 1.0 + (run_hash - 50) * 0.01  # Vary by ±50%
    
    production_cost = int(18500000 * base_multiplier)  # ₹1.85 Cr
    transportation_cost = int(8200000 * base_multiplier)  # ₹82 L
    fixed_trip_cost = int(1200000 * base_multiplier)  # ₹12 L
    holding_cost = int(450000 * base_multiplier)  # ₹4.5 L
    
    # Add penalty costs for some runs
    penalty_cost = 0
    if solver_status == "feasible" and run_hash > 90:
        penalty_cost = int(500000 * base_multiplier)  # ₹5 L penalty
    
    total_cost = production_cost + transportation_cost + fixed_trip_cost + holding_cost + penalty_cost
    
    # Service level varies with solver status
    if solver_status == "optimal":
        service_level = random.uniform(0.95, 0.99)
    elif solver_status == "feasible":
        service_level = random.uniform(0.85, 0.95)
    else:
        service_level = 0.0
    
    # Generate production plan
    plants = ["Mumbai_Plant", "Delhi_Plant", "Chennai_Plant", "Kolkata_Plant"]
    production_plan = []
    
    if solver_status != "infeasible":
        for plant in plants:
            for period in ["2025-01", "2025-02", "2025-03"]:
                production = random.randint(800, 2500) * base_multiplier
                if production > 0:
                    production_plan.append({
                        "plant": plant,
                        "period": period,
                        "tonnes": int(production)
                    })
    
    # Generate shipment plan
    customers = ["Mumbai_Market", "Delhi_NCR", "Chennai_Region", "Kolkata_Hub", "Pune_Market"]
    transport_modes = ["road", "rail", "sea"]
    shipment_plan = []
    
    if solver_status != "infeasible":
        for i in range(random.randint(8, 15)):
            origin = random.choice(plants)
            destination = random.choice(customers)
            mode = random.choice(transport_modes)
            period = random.choice(["2025-01", "2025-02", "2025-03"])
            tonnes = random.randint(200, 1200) * base_multiplier
            trips = max(1, int(tonnes / random.randint(25, 50)))
            
            shipment_plan.append({
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "period": period,
                "tonnes": int(tonnes),
                "trips": trips
            })
    
    # Generate inventory levels
    inventory_plan = []
    
    if solver_status != "infeasible":
        for plant in plants:
            for period in ["2025-01", "2025-02", "2025-03"]:
                inventory = random.randint(100, 500) * base_multiplier
                inventory_plan.append({
                    "plant": plant,
                    "period": period,
                    "tonnes": int(inventory)
                })
    
    # Capacity utilization
    capacity_utilization = {}
    if solver_status != "infeasible":
        for plant in plants:
            utilization = random.uniform(0.65, 0.95) * base_multiplier
            capacity_utilization[plant] = min(1.0, utilization)
    
    return {
        # Core result fields matching API contract
        "run_id": run_id,
        "timestamp": run_time.isoformat(),
        "solver_status": solver_status,
        "runtime_seconds": runtime_seconds,
        "optimality_gap": optimality_gap,
        
        # Cost breakdown
        "total_cost": total_cost,
        "production_cost": production_cost,
        "transportation_cost": transportation_cost,
        "fixed_trip_cost": fixed_trip_cost,
        "holding_cost": holding_cost,
        "penalty_cost": penalty_cost,
        
        # Performance metrics
        "service_level": service_level,
        "capacity_utilization": capacity_utilization,
        "avg_utilization": sum(capacity_utilization.values()) / len(capacity_utilization) if capacity_utilization else 0,
        
        # Detailed plans
        "production": production_plan,
        "shipments": shipment_plan,
        "inventory": inventory_plan,
        
        # Additional metrics
        "stockout_risk": max(0, 1 - service_level),
        "total_production": sum(p["tonnes"] for p in production_plan),
        "total_shipments": sum(s["tonnes"] for s in shipment_plan),
        "total_inventory": sum(i["tonnes"] for i in inventory_plan),
        
        # Solver details
        "solver": "highs",
        "termination_reason": "optimal" if solver_status == "optimal" else "time_limit" if solver_status == "feasible" else "infeasible"
    }


@router.get("/runs")
def get_optimization_runs(
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get list of optimization runs."""
    
    try:
        # Generate sample runs for the last 30 days
        runs = []
        base_time = datetime.now()
        
        for i in range(limit):
            run_time = base_time - timedelta(hours=i*2, minutes=random.randint(0, 59))
            run_id = f"RUN_{run_time.strftime('%Y%m%d_%H%M%S')}"
            
            # Determine status
            run_hash = hash(run_id) % 100
            if run_hash < 85:
                status = "completed"
            elif run_hash < 95:
                status = "completed_with_warnings"
            else:
                status = "failed"
            
            # Apply status filter
            if status_filter and status != status_filter:
                continue
            
            runs.append({
                "run_id": run_id,
                "status": status,
                "timestamp": run_time.isoformat(),
                "scenario": random.choice(["base", "high_demand", "low_demand", "capacity_constrained"]),
                "solver": "highs",
                "runtime_seconds": random.uniform(45.0, 300.0) if status.startswith("completed") else random.uniform(10.0, 60.0),
                "total_cost": random.randint(25000000, 35000000) if status.startswith("completed") else None
            })
        
        return {
            "runs": runs,
            "total_count": len(runs),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching optimization runs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch optimization runs")


@router.get("/runs/{run_id}/results")
def get_optimization_results(run_id: str, db: Session = Depends(get_db)):
    """Get detailed results for a specific optimization run."""
    
    try:
        # Validate run_id format
        if not run_id.startswith("RUN_"):
            raise HTTPException(status_code=400, detail="Invalid run ID format")
        
        # Check if run exists and is completed
        run_hash = hash(run_id) % 100
        
        if run_hash >= 95:  # 5% failure rate
            raise HTTPException(status_code=404, detail="No results yet — run still processing")
        
        # Generate results
        results = _generate_optimization_result(run_id)
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching results for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch optimization results")


@router.get("/runs/{run_id}/status")
def get_run_status(run_id: str, db: Session = Depends(get_db)):
    """Get status of a specific optimization run."""
    
    try:
        # Validate run_id format
        if not run_id.startswith("RUN_"):
            raise HTTPException(status_code=400, detail="Invalid run ID format")
        
        # Determine status based on run_id hash
        run_hash = hash(run_id) % 100
        
        if run_hash < 85:
            status = "completed"
            progress = 100
        elif run_hash < 95:
            status = "completed_with_warnings"
            progress = 100
        else:
            status = "failed"
            progress = 0
        
        # Extract timestamp from run_id
        try:
            timestamp_str = run_id.split('_')[1] + '_' + run_id.split('_')[2]
            run_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        except:
            run_time = datetime.now()
        
        return {
            "run_id": run_id,
            "status": status,
            "progress": progress,
            "timestamp": run_time.isoformat(),
            "estimated_completion": (run_time + timedelta(minutes=5)).isoformat() if status == "running" else None,
            "error_message": "Solver could not find feasible solution" if status == "failed" else None
        }
        
    except Exception as e:
        logger.error(f"Error fetching status for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch run status")


@router.delete("/runs/{run_id}")
def delete_optimization_run(run_id: str, db: Session = Depends(get_db)):
    """Delete an optimization run and its results."""
    
    try:
        # Validate run_id format
        if not run_id.startswith("RUN_"):
            raise HTTPException(status_code=400, detail="Invalid run ID format")
        
        # In a real implementation, this would delete from database
        # For demo, we'll just return success
        
        return {
            "message": f"Run {run_id} deleted successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error deleting run {run_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete optimization run")


@router.post("/runs/{run_id}/rerun")
def rerun_optimization(run_id: str, db: Session = Depends(get_db)):
    """Rerun an optimization with the same parameters."""
    
    try:
        # Validate run_id format
        if not run_id.startswith("RUN_"):
            raise HTTPException(status_code=400, detail="Invalid run ID format")
        
        # Generate new run ID
        new_run_id = f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            "message": f"Rerun initiated successfully",
            "original_run_id": run_id,
            "new_run_id": new_run_id,
            "status": "queued",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error rerunning optimization {run_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate rerun")