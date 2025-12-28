from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.core.deps import get_db
from app.schemas.kpi import KPIDashboard, ScenarioComparison
from app.services.audit_service import audit_timer

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard/{scenario_name}")
async def get_kpi_dashboard(
    scenario_name: str,
    run_id: Optional[str] = Query(None, description="Specific run ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Return KPIs for a given scenario with enterprise-grade error handling.
    """
    try:
        with audit_timer("system", "kpi_dashboard_fetch", db):
            # Mock implementation - in production would fetch from database
            if scenario_name == "base":
                kpis = {
                    "scenario_name": "base",
                    "run_id": run_id or "base_run_001",
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_cost": 1450000.0,
                    "cost_breakdown": {
                        "production_cost": 1250000.0,
                        "transport_cost": 150000.0,
                        "fixed_trip_cost": 30000.0,
                        "holding_cost": 20000.0,
                        "penalty_cost": 0.0
                    },
                    "production_utilization": {
                        "PLANT_001": 0.85,
                        "PLANT_002": 0.72,
                        "PLANT_003": 0.91
                    },
                    "transport_utilization": {
                        "TRUCK": 0.78,
                        "RAIL": 0.65,
                        "SHIP": 0.82
                    },
                    "inventory_metrics": {
                        "safety_stock_compliance": 0.96,
                        "average_inventory_days": 15.2,
                        "stockout_events": 0,
                        "inventory_turns": 24.1
                    },
                    "service_performance": {
                        "demand_fulfillment_rate": 0.98,
                        "on_time_delivery": 0.95,
                        "average_lead_time_days": 3.2,
                        "service_level": 0.97
                    },
                    "data_sources": {
                        "primary": "internal",
                        "external_used": False,
                        "quarantine_count": 0
                    }
                }
            elif scenario_name == "high_demand":
                kpis = {
                    "scenario_name": "high_demand",
                    "run_id": run_id or "high_run_001",
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_cost": 1850000.0,
                    "cost_breakdown": {
                        "production_cost": 1600000.0,
                        "transport_cost": 180000.0,
                        "fixed_trip_cost": 45000.0,
                        "holding_cost": 25000.0,
                        "penalty_cost": 0.0
                    },
                    "production_utilization": {
                        "PLANT_001": 0.95,
                        "PLANT_002": 0.88,
                        "PLANT_003": 0.98
                    },
                    "transport_utilization": {
                        "TRUCK": 0.92,
                        "RAIL": 0.85,
                        "SHIP": 0.91
                    },
                    "inventory_metrics": {
                        "safety_stock_compliance": 0.88,
                        "average_inventory_days": 12.8,
                        "stockout_events": 2,
                        "inventory_turns": 28.5
                    },
                    "service_performance": {
                        "demand_fulfillment_rate": 0.94,
                        "on_time_delivery": 0.89,
                        "average_lead_time_days": 4.1,
                        "service_level": 0.92
                    },
                    "data_sources": {
                        "primary": "internal",
                        "external_used": False,
                        "quarantine_count": 0
                    }
                }
            else:
                # Default fallback for unknown scenarios
                kpis = {
                    "scenario_name": scenario_name,
                    "run_id": run_id or "unknown_run_001",
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_cost": 0.0,
                    "cost_breakdown": {
                        "production_cost": 0.0,
                        "transport_cost": 0.0,
                        "fixed_trip_cost": 0.0,
                        "holding_cost": 0.0,
                        "penalty_cost": 0.0
                    },
                    "production_utilization": {},
                    "transport_utilization": {},
                    "inventory_metrics": {
                        "safety_stock_compliance": 0.0,
                        "average_inventory_days": 0.0,
                        "stockout_events": 0,
                        "inventory_turns": 0.0
                    },
                    "service_performance": {
                        "demand_fulfillment_rate": 0.0,
                        "on_time_delivery": 0.0,
                        "average_lead_time_days": 0.0,
                        "service_level": 0.0
                    },
                    "data_sources": {
                        "primary": "internal",
                        "external_used": False,
                        "quarantine_count": 0
                    }
                }
            
            return kpis
            
    except Exception as e:
        logger.error(f"Failed to fetch KPI dashboard for {scenario_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/compare")
async def compare_scenarios(
    scenario_names: List[str],
    run_ids: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Compare KPIs across multiple scenarios with robust error handling.
    """
    try:
        with audit_timer("system", "kpi_scenario_comparison", db):
            comparison = {
                "comparison_timestamp": datetime.utcnow().isoformat(),
                "scenarios": [],
                "summary_metrics": {}
            }
            
            total_costs = []
            service_levels = []
            
            for i, scenario_name in enumerate(scenario_names):
                run_id = run_ids[i] if run_ids and i < len(run_ids) else None
                
                # Fetch individual scenario KPIs
                try:
                    scenario_kpis = await get_kpi_dashboard(scenario_name, run_id, db)
                    comparison["scenarios"].append(scenario_kpis)
                    
                    total_costs.append(scenario_kpis["total_cost"])
                    service_levels.append(scenario_kpis["service_performance"]["service_level"])
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch KPIs for scenario {scenario_name}: {e}")
                    # Add placeholder for failed scenario
                    comparison["scenarios"].append({
                        "scenario_name": scenario_name,
                        "error": f"Failed to load: {str(e)}",
                        "total_cost": 0.0,
                        "service_performance": {"service_level": 0.0}
                    })
                    total_costs.append(0.0)
                    service_levels.append(0.0)
            
            # Calculate summary metrics
            if total_costs and service_levels:
                comparison["summary_metrics"] = {
                    "cost_range": {
                        "min": min(total_costs),
                        "max": max(total_costs),
                        "avg": sum(total_costs) / len(total_costs)
                    },
                    "service_level_range": {
                        "min": min(service_levels),
                        "max": max(service_levels),
                        "avg": sum(service_levels) / len(service_levels)
                    },
                    "cost_variance": max(total_costs) - min(total_costs),
                    "service_variance": max(service_levels) - min(service_levels)
                }
            
            return comparison
            
    except Exception as e:
        logger.error(f"Failed to compare scenarios: {e}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.get("/summary")
async def get_kpi_summary(
    period_hours: int = Query(24, description="Time period in hours"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get summary KPIs for the specified time period.
    """
    try:
        with audit_timer("system", "kpi_summary_fetch", db):
            # Mock summary data
            summary = {
                "period_hours": period_hours,
                "summary_timestamp": datetime.utcnow().isoformat(),
                "total_runs": 12,
                "successful_runs": 11,
                "failed_runs": 1,
                "average_total_cost": 1523456.78,
                "average_service_level": 0.945,
                "cost_trend": "stable",  # increasing, decreasing, stable
                "service_trend": "improving",
                "top_performers": {
                    "lowest_cost": {"scenario": "base", "cost": 1450000.0},
                    "highest_service": {"scenario": "base", "service_level": 0.98}
                },
                "issues": [
                    {
                        "type": "solver_timeout",
                        "count": 1,
                        "scenario": "high_demand_extreme"
                    }
                ]
            }
            
            return summary
            
    except Exception as e:
        logger.error(f"Failed to fetch KPI summary: {e}")
        raise HTTPException(status_code=500, detail=f"Summary fetch failed: {str(e)}")


@router.get("/health")
async def kpi_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check endpoint for KPI service.
    """
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "kpi_api",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"KPI health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "kpi_api",
            "error": str(e)
        }
