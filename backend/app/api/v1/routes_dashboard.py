"""
Dashboard API Routes

Provides endpoints for the production-ready dashboard system including:
- Data health status
- Data validation reports  
- Clean data previews
- Optimization execution
- Results visualization
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
import logging

from app.core.deps import get_db, get_current_user
from app.core.rbac import Permission, role_has_permission
from app.services.data_health_service import get_data_health_overview
from app.services.data_validation_service import run_comprehensive_validation
from app.services.clean_data_service import (
    get_clean_data_for_optimization,
    get_clean_data_preview,
    get_all_clean_data_previews
)
from app.services.optimization.model_builder import build_clinker_model
from app.services.optimization.solvers import solve_model
from app.services.optimization.result_parser import extract_solution
from app.services.kpi_calculator import compute_kpis
from app.services.scenarios.scenario_runner import run_single_scenario_from_config
from app.services.scenarios.scenario_generator import ScenarioConfig
from app.utils.exceptions import DataValidationError, OptimizationError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health-status")
def get_data_health_status(
    db: Session = Depends(get_db)
):
    """
    Get comprehensive data health status for all tables.
    
    Returns top-level KPIs indicating whether data is ready for optimization.
    """
    
    try:
        health_status = get_data_health_overview(db)
        return health_status
    except Exception as e:
        logger.error(f"Error getting data health status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get data health status: {str(e)}")


@router.get("/validation-report")
def get_validation_report(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Run comprehensive 5-stage validation pipeline and return detailed report.
    
    Stages:
    1. Schema validation
    2. Business rule validation
    3. Referential integrity
    4. Unit consistency  
    5. Missing data scan
    """
    
    if not role_has_permission(current_user.get("role"), Permission.READ_DATA):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        validation_result = run_comprehensive_validation(db)
        return validation_result
    except Exception as e:
        logger.error(f"Error running validation report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run validation: {str(e)}")


@router.get("/validation-report/csv")
def download_validation_report_csv(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Download validation report as CSV file."""
    
    if not role_has_permission(current_user.get("role"), Permission.READ_DATA):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        validation_result = run_comprehensive_validation(db)
        csv_content = validation_result.get("error_report_csv", "")
        
        from fastapi.responses import Response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=validation_report.csv"}
        )
    except Exception as e:
        logger.error(f"Error downloading validation CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate CSV: {str(e)}")


@router.get("/raw-data/{table_name}")
def get_raw_data_preview(
    table_name: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get paginated preview of raw data from database tables.
    
    Supported tables:
    - plant_master
    - production_capacity_cost
    - transport_routes_modes
    - demand_forecast
    - initial_inventory
    - safety_stock_policy
    """
    
    if not role_has_permission(current_user.get("role"), Permission.READ_DATA):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Map table names to models
    from app.db.models.plant_master import PlantMaster
    from app.db.models.production_capacity_cost import ProductionCapacityCost
    from app.db.models.transport_routes_modes import TransportRoutesModes
    from app.db.models.demand_forecast import DemandForecast
    from app.db.models.initial_inventory import InitialInventory
    from app.db.models.safety_stock_policy import SafetyStockPolicy
    
    table_models = {
        "plant_master": PlantMaster,
        "production_capacity_cost": ProductionCapacityCost,
        "transport_routes_modes": TransportRoutesModes,
        "demand_forecast": DemandForecast,
        "initial_inventory": InitialInventory,
        "safety_stock_policy": SafetyStockPolicy
    }
    
    if table_name not in table_models:
        raise HTTPException(status_code=400, detail=f"Unknown table: {table_name}")
    
    try:
        model = table_models[table_name]
        
        # Get total count
        total_count = db.query(model).count()
        
        # Get paginated data
        records = db.query(model).offset(offset).limit(limit).all()
        
        # Convert to dict format
        data = []
        for record in records:
            record_dict = {}
            for column in model.__table__.columns:
                value = getattr(record, column.name)
                # Convert datetime to string for JSON serialization
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                record_dict[column.name] = value
            data.append(record_dict)
        
        return {
            "table_name": table_name,
            "data": data,
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            },
            "columns": [col.name for col in model.__table__.columns]
        }
        
    except Exception as e:
        logger.error(f"Error getting raw data for {table_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get raw data: {str(e)}")


@router.get("/clean-data/{table_name}")
def get_clean_data_table_preview(
    table_name: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get preview of cleaned data that will be used by the optimization model.
    
    This shows the FINAL cleaned dataset after all normalization and validation.
    """
    
    if not role_has_permission(current_user.get("role"), Permission.READ_DATA):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        clean_preview = get_clean_data_preview(db, table_name, limit)
        return clean_preview
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting clean data preview for {table_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get clean data: {str(e)}")


@router.get("/clean-data")
def get_all_clean_data_previews_endpoint(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get previews of all cleaned data tables."""
    
    if not role_has_permission(current_user.get("role"), Permission.READ_DATA):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        previews = get_all_clean_data_previews(db, limit)
        return previews
    except Exception as e:
        logger.error(f"Error getting all clean data previews: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get clean data previews: {str(e)}")


@router.post("/run-optimization")
def run_optimization(
    background_tasks: BackgroundTasks,
    solver: str = Query("highs", description="Solver to use: highs, cbc, gurobi"),
    time_limit: int = Query(600, ge=60, le=3600, description="Time limit in seconds"),
    mip_gap: float = Query(0.01, ge=0.001, le=0.1, description="MIP gap tolerance"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Run optimization with clean, validated data.
    
    Button is enabled ONLY IF all validation stages pass.
    Returns job ID for status tracking.
    """
    
    if not role_has_permission(current_user.get("role"), Permission.RUN_OPTIMIZATION):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        # First check if data is ready for optimization
        validation_result = run_comprehensive_validation(db)
        
        if not validation_result["optimization_ready"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Optimization blocked due to validation failures",
                    "validation_summary": validation_result["summary"],
                    "total_errors": validation_result["summary"]["total_errors"]
                }
            )
        
        # Get clean data for optimization
        clean_data = get_clean_data_for_optimization(db, validate_first=False)  # Already validated
        
        # Build and solve model
        model = build_clinker_model(clean_data)
        solver_result = solve_model(model, solver_name=solver, time_limit_seconds=time_limit, mip_gap=mip_gap)
        solution = extract_solution(model)
        
        # Compute KPIs
        kpis = compute_kpis(
            costs=solution.get("costs", {}),
            demand={},  # TODO: Extract from solution
            fulfilled={},  # TODO: Extract from solution  
            plant_production={},  # TODO: Extract from solution
            plant_capacity={}  # TODO: Extract from solution
        )
        
        return {
            "status": "completed",
            "solver_result": solver_result,
            "solution": solution,
            "kpis": kpis,
            "data_metadata": clean_data["metadata"]
        }
        
    except DataValidationError as e:
        raise HTTPException(status_code=400, detail=f"Data validation failed: {str(e)}")
    except OptimizationError as e:
        raise HTTPException(status_code=400, detail=f"Optimization failed: {str(e)}")
    except Exception as e:
        logger.error(f"Error running optimization: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get("/optimization-status/{job_id}")
def get_optimization_status(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get status of optimization job."""
    
    if not role_has_permission(current_user.get("role"), Permission.READ_DATA):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # TODO: Implement job status tracking with Celery or similar
    return {
        "job_id": job_id,
        "status": "not_implemented",
        "message": "Job status tracking not yet implemented"
    }


@router.post("/run-scenario")
def run_single_scenario(
    scenario_config: ScenarioConfig,
    solver: str = Query("highs"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Run a single scenario with the given configuration."""
    
    if not role_has_permission(current_user.get("role"), Permission.RUN_OPTIMIZATION):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        # Get clean data
        clean_data = get_clean_data_for_optimization(db)
        
        # Convert to the format expected by scenario runner
        data_dict = {
            "plants": clean_data["plants"],
            "production_capacity_cost": clean_data["production_capacity_cost"],
            "transport_routes_modes": clean_data["transport_routes_modes"],
            "demand_forecast": clean_data["demand_forecast"],
            "safety_stock_policy": clean_data["safety_stock_policy"],
            "initial_inventory": clean_data["initial_inventory"],
            "time_periods": clean_data["time_periods"]
        }
        
        # Run scenario
        result = run_single_scenario_from_config(data_dict, scenario_config, solver)
        
        return result
        
    except Exception as e:
        logger.error(f"Error running scenario: {e}")
        raise HTTPException(status_code=500, detail=f"Scenario execution failed: {str(e)}")


@router.get("/results/{run_id}")
def get_optimization_results(
    run_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get optimization results for a specific run."""
    
    if not role_has_permission(current_user.get("role"), Permission.READ_DATA):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # TODO: Implement results storage and retrieval
    return {
        "run_id": run_id,
        "status": "not_implemented",
        "message": "Results storage not yet implemented"
    }


@router.get("/results/{run_id}/export")
def export_optimization_results(
    run_id: str,
    format: str = Query("json", regex="^(json|csv|pdf)$"),
    current_user: dict = Depends(get_current_user)
):
    """Export optimization results in specified format."""
    
    if not role_has_permission(current_user.get("role"), Permission.READ_DATA):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # TODO: Implement results export
    return {
        "run_id": run_id,
        "format": format,
        "status": "not_implemented",
        "message": "Results export not yet implemented"
    }