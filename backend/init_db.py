#!/usr/bin/env python3
"""
Initialize the database with required tables.
Includes all new production-ready models.
"""

from app.db.session import engine
from app.db.base import Base

# Import all models to ensure they're registered with Base
from app.db.models.audit_log import AuditLog
from app.db.models.plant_master import PlantMaster
from app.db.models.production_capacity_cost import ProductionCapacityCost
from app.db.models.transport_routes_modes import TransportRoutesModes
from app.db.models.demand_forecast import DemandForecast
from app.db.models.initial_inventory import InitialInventory
from app.db.models.safety_stock_policy import SafetyStockPolicy
from app.db.models.optimization_run import OptimizationRun
from app.db.models.optimization_results import OptimizationResults
from app.db.models.kpi_snapshot import KPISnapshot

# New production-ready models
from app.db.models.job_status import JobStatusTable
from app.db.models.user import User, Role, UserSession
from app.db.models.kpi_precomputed import KPIPrecomputed, KPIAggregated
from app.db.models.scenario import Scenario, ScenarioComparison

def init_db():
    """Create all database tables."""
    print("Creating database tables...")
    print("This includes:")
    print("  - Core tables (plants, demand, routes, etc.)")
    print("  - Job queue tables (job_status)")
    print("  - RBAC tables (users, roles, user_sessions)")
    print("  - KPI tables (kpi_precomputed, kpi_aggregated)")
    print("  - Scenario tables (scenarios, scenario_comparison)")
    print("  - Audit log table")
    
    Base.metadata.create_all(bind=engine)
    print("\n✓ Database tables created successfully!")
    print("✓ SQLite WAL mode will be enabled on first connection")

if __name__ == "__main__":
    init_db()