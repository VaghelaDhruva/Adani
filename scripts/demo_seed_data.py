#!/usr/bin/env python3
"""
Seed demo data into the database for testing and demos.
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.orm import Session
from app.db.base import SessionLocal, engine
from app.db.models import PlantMaster, ProductionCapacityCost, TransportRoutesModes, DemandForecast, SafetyStockPolicy, InitialInventory, ScenarioMetadata
from app.core.security import get_password_hash
from datetime import datetime, timedelta


def seed():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        # Plants
        plants = [
            PlantMaster(plant_id="P1", plant_name="North Plant", plant_type="clinker", latitude=28.6, longitude=77.2, region="North", country="IN"),
            PlantMaster(plant_id="P2", plant_name="South Plant", plant_type="clinker", latitude=12.9, longitude=77.6, region="South", country="IN"),
            PlantMaster(plant_id="C1", plant_name="Customer A", plant_type="customer", latitude=19.0, longitude=72.8, region="West", country="IN"),
        ]
        for p in plants:
            db.merge(p)

        # Production capacity
        periods = [("2025-W01",), ("2025-W02",), ("2025-W03",)]
        for plant in ["P1", "P2"]:
            for (period,) in periods:
                db.merge(ProductionCapacityCost(
                    plant_id=plant,
                    period=period,
                    max_capacity_tonnes=2000.0,
                    variable_cost_per_tonne=5.0,
                    fixed_cost_per_period=500.0,
                ))

        # Transport routes (road only for demo)
        routes = [
            TransportRoutesModes(origin_plant_id="P1", destination_node_id="C1", transport_mode="road", distance_km=1200.0, cost_per_tonne=2.5, vehicle_capacity_tonnes=40.0, min_batch_quantity_tonnes=0.0),
            TransportRoutesModes(origin_plant_id="P2", destination_node_id="C1", transport_mode="road", distance_km=600.0, cost_per_tonne=2.2, vehicle_capacity_tonnes=40.0, min_batch_quantity_tonnes=0.0),
        ]
        for r in routes:
            db.merge(r)

        # Demand forecast
        for period in periods:
            db.merge(DemandForecast(customer_node_id="C1", period=period[0], demand_tonnes=800.0, source="demo"))

        # Safety stock policy
        db.merge(SafetyStockPolicy(node_id="C1", policy_type="days_of_cover", policy_value=7.0, safety_stock_tonnes=210.0))

        # Initial inventory
        db.merge(InitialInventory(node_id="P1", period="2025-W01", inventory_tonnes=100.0))
        db.merge(InitialInventory(node_id="P2", period="2025-W01", inventory_tonnes=80.0))

        # Scenario metadata
        db.merge(ScenarioMetadata(scenario_name="base", description="Base case scenario", demand_multiplier=1.0, transport_cost_multiplier=1.0, production_cost_multiplier=1.0, status="draft", created_by="demo"))

        db.commit()
        print("Demo data seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
