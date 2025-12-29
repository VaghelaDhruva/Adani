#!/usr/bin/env python3
"""
Initialize the database with required tables.
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

def init_db():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()