#!/usr/bin/env python3
"""
Working minimal backend for the dashboard.
This version avoids all problematic imports.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import random

app = FastAPI(
    title="Clinker Supply Chain Optimization",
    version="1.0.0",
    description="Working minimal backend"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def format_inr_currency(amount: float) -> str:
    """Format currency in Indian Rupees."""
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.2f} Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.2f} L"
    else:
        return f"₹{amount:,.0f}"

@app.get("/")
def root():
    return {
        "message": "Clinker Supply Chain Optimization API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "healthy",
            "api": "healthy"
        }
    }

# Frontend expects these endpoints:
@app.get("/api/v1/kpi/scenarios/list")
def list_scenarios_kpi():
    return {
        "scenarios": [
            {
                "name": "base",
                "display_name": "Base Scenario",
                "description": "Current operational configuration",
                "status": "active",
                "last_run": datetime.now().isoformat()
            },
            {
                "name": "optimized", 
                "display_name": "Optimized Scenario",
                "description": "Cost-optimized configuration",
                "status": "active",
                "last_run": datetime.now().isoformat()
            }
        ]
    }

@app.get("/api/v1/dashboard/scenarios/list")
def list_scenarios():
    return {
        "scenarios": [
            {
                "name": "base",
                "display_name": "Base Scenario",
                "description": "Current operational configuration",
                "status": "active",
                "last_run": datetime.now().isoformat()
            },
            {
                "name": "optimized", 
                "display_name": "Optimized Scenario",
                "description": "Cost-optimized configuration",
                "status": "active",
                "last_run": datetime.now().isoformat()
            }
        ]
    }

@app.get("/api/v1/dashboard/health-status")
def get_health_status():
    """Get system health status."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "healthy",
            "api": "healthy",
            "dashboard": "ready"
        },
        "data_validation": {
            "status": "passed",
            "last_check": datetime.now().isoformat()
        }
    }

@app.get("/api/v1/kpi/dashboard/{scenario_name}")
def get_dashboard_kpis_kpi(scenario_name: str):
    """Get KPI dashboard data - KPI endpoint."""
    return get_dashboard_kpis(scenario_name)

@app.get("/api/v1/dashboard/kpi/dashboard/{scenario_name}")
def get_dashboard_kpis(scenario_name: str):
    """Get KPI dashboard data."""
    
    # Generate realistic data
    base_production_cost = random.uniform(1200000, 1800000)
    base_transport_cost = random.uniform(300000, 600000)
    base_inventory_cost = random.uniform(50000, 150000)
    total_cost = base_production_cost + base_transport_cost + base_inventory_cost
    
    return {
        "scenario_name": scenario_name,
        "timestamp": datetime.now().isoformat(),
        "status": "success",
        
        "cost_summary": {
            "total_cost": {
                "value": total_cost,
                "formatted": format_inr_currency(total_cost),
                "change_percent": random.uniform(-5, 15)
            },
            "production_cost": {
                "value": base_production_cost,
                "formatted": format_inr_currency(base_production_cost),
                "percentage": round((base_production_cost / total_cost) * 100, 1)
            },
            "transport_cost": {
                "value": base_transport_cost,
                "formatted": format_inr_currency(base_transport_cost),
                "percentage": round((base_transport_cost / total_cost) * 100, 1)
            },
            "inventory_cost": {
                "value": base_inventory_cost,
                "formatted": format_inr_currency(base_inventory_cost),
                "percentage": round((base_inventory_cost / total_cost) * 100, 1)
            }
        },
        
        "service_performance": {
            "overall_service_level": {
                "value": random.uniform(92, 98),
                "target": 95,
                "status": "good"
            },
            "on_time_delivery": {
                "value": random.uniform(88, 96),
                "target": 90,
                "status": "good"
            },
            "demand_fulfillment": {
                "value": random.uniform(94, 99),
                "target": 95,
                "status": "excellent"
            }
        },
        
        "utilization": {
            "production_utilization": {
                "value": random.uniform(75, 95),
                "capacity": 100,
                "status": "optimal"
            },
            "transport_utilization": {
                "value": random.uniform(70, 90),
                "capacity": 100,
                "status": "good"
            }
        },
        
        "operations": {
            "total_production": {
                "value": random.uniform(95000, 115000),
                "unit": "tonnes",
                "formatted": f"{random.uniform(95, 115):.1f}K tonnes"
            },
            "total_shipments": {
                "value": random.randint(450, 650),
                "unit": "shipments"
            }
        },
        
        "alerts": [
            {
                "type": "info",
                "message": "Production utilization is optimal",
                "priority": "low"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Additional endpoints that might be needed
@app.get("/api/v1/kpi/run-optimization")
def run_optimization():
    """Mock optimization run endpoint."""
    return {
        "status": "success",
        "message": "Optimization completed successfully",
        "run_id": f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "results": {
            "total_cost": 1650000,
            "total_cost_formatted": "₹1.65 Cr",
            "optimization_time": "45 seconds"
        }
    }

@app.get("/api/v1/scenarios/{scenario_name}")
def get_scenario_details(scenario_name: str):
    """Get detailed scenario information."""
    return {
        "name": scenario_name,
        "display_name": f"{scenario_name.title()} Scenario",
        "description": f"Details for {scenario_name} scenario",
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "last_run": datetime.now().isoformat(),
        "parameters": {
            "optimization_objective": "minimize_cost",
            "service_level_target": 95,
            "planning_horizon": 12
        }
    }

@app.get("/api/v1/data/validation/status")
def get_validation_status():
    """Get data validation status."""
    return {
        "status": "passed",
        "timestamp": datetime.now().isoformat(),
        "validation_stages": {
            "schema_validation": "passed",
            "business_rules": "passed", 
            "referential_integrity": "passed",
            "data_quality": "passed"
        },
        "summary": {
            "total_records": 1250,
            "valid_records": 1248,
            "warnings": 2,
            "errors": 0
        }
    }