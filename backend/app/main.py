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
    routes_scenarios,
)

setup_logging()
settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    version="1.0.0",
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


@app.get("/")
def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}
