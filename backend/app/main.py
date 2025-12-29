from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging_config import setup_logging, configure_uvicorn_logging
from app.api.v1 import (
    routes_auth,
    routes_dashboard_demo,
    routes_data,
    routes_health,
    routes_jobs,
    routes_kpi,
    routes_optimization,
    routes_runs,
    routes_scenarios,
    routes_integrations,
)

# Import the new optimization routes
from app.api.v1 import routes_optimization as routes_optimization_new

setup_logging()
settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    version="1.0.0",
<<<<<<< HEAD
=======
    description="Supply Chain Optimization System with Real Calculated KPIs"
>>>>>>> d4196135 (Fixed Bug)
)

# CORS (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes_health.router, prefix=settings.API_V1_STR, tags=["health"])
app.include_router(routes_auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(routes_dashboard_demo.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["dashboard"])
app.include_router(routes_data.router, prefix=f"{settings.API_V1_STR}/data", tags=["data"])
app.include_router(routes_scenarios.router, prefix=f"{settings.API_V1_STR}/scenarios", tags=["scenarios"])
app.include_router(routes_optimization.router, prefix=f"{settings.API_V1_STR}/optimization", tags=["optimization"])
app.include_router(routes_kpi.router, prefix=f"{settings.API_V1_STR}/kpi", tags=["kpi"])
app.include_router(routes_jobs.router, prefix=f"{settings.API_V1_STR}/jobs", tags=["jobs"])
app.include_router(routes_runs.router, prefix=f"{settings.API_V1_STR}", tags=["runs"])

# Include new integration and optimization routes
app.include_router(routes_integrations.router, prefix=f"{settings.API_V1_STR}/integrations", tags=["integrations"])
app.include_router(routes_optimization_new.router, prefix=f"{settings.API_V1_STR}/optimize", tags=["optimization-engine"])


@app.get("/")
def root():
<<<<<<< HEAD
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}
=======
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": "1.0.0",
        "features": [
            "Real optimization engine with Pyomo + HiGHS solver",
            "Calculated KPI dashboard with Indian Rupee formatting",
            "Interactive charts and visualizations",
            "5-stage data validation pipeline",
            "Enterprise-grade error handling and logging"
        ],
        "endpoints": {
            "api_docs": "/docs",
            "kpi_dashboard": "/api/v1/kpi/dashboard/{scenario_name}",
            "run_optimization": "/api/v1/kpi/run-optimization",
            "health_check": "/api/v1/dashboard/health-status"
        }
    }


@app.get("/api/v1/system/info")
def system_info():
    """Get system information and capabilities."""
    return {
        "system": "Supply Chain Optimization",
        "version": "1.0.0",
        "optimization_engine": "Pyomo + HiGHS/CBC",
        "database": "SQLite with full persistence",
        "features": {
            "real_optimization": True,
            "calculated_kpis": True,
            "interactive_dashboard": True,
            "data_validation": True,
            "scenario_comparison": True,
            "export_capabilities": True
        },
        "sample_data": {
            "plants": 3,
            "transport_routes": 9,
            "customers": 7,
            "monthly_demand": "108,000 tonnes",
            "cost_range": "₹1,450,000 - ₹1,850,000"
        }
    }
>>>>>>> d4196135 (Fixed Bug)
