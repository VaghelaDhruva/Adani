#!/usr/bin/env python3
"""
Production Database Setup with ETL Pipeline
Creates all tables and populates them with realistic supply chain data
"""

import sys
import os
sys.path.append('.')

from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.base import Base
import logging

# Import all models to ensure they're registered
from app.db.models.plant_master import PlantMaster
from app.db.models.demand_forecast import DemandForecast
from app.db.models.transport_routes_modes import TransportRoutesModes
from app.db.models.production_capacity_cost import ProductionCapacityCost
from app.db.models.safety_stock_policy import SafetyStockPolicy
from app.db.models.initial_inventory import InitialInventory
from app.db.models.optimization_run import OptimizationRun
from app.db.models.optimization_results import OptimizationResults
from app.db.models.kpi_snapshot import KPISnapshot
from app.db.models.scenario_metadata import ScenarioMetadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_all_tables():
    """Create all database tables"""
    logger.info("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ All tables created successfully")

def load_plant_master_data(db: Session):
    """Load plant master data"""
    logger.info("Loading plant master data...")
    
    plants_data = [
        {
            "plant_id": "PLANT_001",
            "plant_name": "Ambuja Cement - Dadri",
            "plant_type": "Integrated",
            "latitude": 28.5706,
            "longitude": 77.5500,
            "region": "North",
            "country": "India",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "plant_id": "PLANT_002", 
            "plant_name": "ACC Cement - Wadi",
            "plant_type": "Integrated",
            "latitude": 17.0568,
            "longitude": 76.9947,
            "region": "South",
            "country": "India",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "plant_id": "PLANT_003",
            "plant_name": "Ambuja Cement - Ropar",
            "plant_type": "Integrated",
            "latitude": 30.9691,
            "longitude": 76.5194,
            "region": "North",
            "country": "India",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    ]
    
    for plant_data in plants_data:
        existing = db.query(PlantMaster).filter(PlantMaster.plant_id == plant_data["plant_id"]).first()
        if not existing:
            plant = PlantMaster(**plant_data)
            db.add(plant)
    
    db.commit()
    logger.info(f"✅ Loaded {len(plants_data)} plants")

def load_production_capacity_data(db: Session):
    """Load production capacity and cost data"""
    logger.info("Loading production capacity data...")
    
    capacity_data = [
        {
            "plant_id": "PLANT_001",
            "period": "2024-01",
            "max_capacity_tonnes": 30000,
            "variable_cost_per_tonne": 2800.0,
            "fixed_cost_per_period": 850000.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "plant_id": "PLANT_002",
            "period": "2024-01", 
            "max_capacity_tonnes": 28000,
            "variable_cost_per_tonne": 2750.0,
            "fixed_cost_per_period": 780000.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "plant_id": "PLANT_003",
            "period": "2024-01",
            "max_capacity_tonnes": 27000,
            "variable_cost_per_tonne": 2900.0,
            "fixed_cost_per_period": 820000.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    ]
    
    for capacity in capacity_data:
        existing = db.query(ProductionCapacityCost).filter(
            ProductionCapacityCost.plant_id == capacity["plant_id"],
            ProductionCapacityCost.period == capacity["period"]
        ).first()
        if not existing:
            capacity_obj = ProductionCapacityCost(**capacity)
            db.add(capacity_obj)
    
    db.commit()
    logger.info(f"✅ Loaded {len(capacity_data)} capacity records")

def load_demand_forecast_data(db: Session):
    """Load demand forecast data"""
    logger.info("Loading demand forecast data...")
    
    # Create customer nodes
    customers = ["CUST_001", "CUST_002", "CUST_003", "CUST_004", "CUST_005", "CUST_006", "CUST_007"]
    
    demand_data = []
    base_demands = [15000, 12000, 18000, 8500, 11000, 9500, 13500]  # Monthly demand per customer
    
    for i, customer in enumerate(customers):
        demand_data.append({
            "customer_node_id": customer,
            "period": "2024-01",
            "demand_tonnes": base_demands[i],
            "demand_low_tonnes": base_demands[i] * 0.9,
            "demand_high_tonnes": base_demands[i] * 1.1,
            "confidence_level": 0.95,
            "source": "forecast_model",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
    
    for demand in demand_data:
        existing = db.query(DemandForecast).filter(
            DemandForecast.customer_node_id == demand["customer_node_id"],
            DemandForecast.period == demand["period"]
        ).first()
        if not existing:
            demand_obj = DemandForecast(**demand)
            db.add(demand_obj)
    
    db.commit()
    logger.info(f"✅ Loaded {len(demand_data)} demand records")

def load_transport_routes_data(db: Session):
    """Load transport routes data"""
    logger.info("Loading transport routes data...")
    
    plants = ["PLANT_001", "PLANT_002", "PLANT_003"]
    customers = ["CUST_001", "CUST_002", "CUST_003", "CUST_004", "CUST_005", "CUST_006", "CUST_007"]
    
    routes_data = []
    base_distances = [150, 200, 180, 220, 170, 190, 160]  # km
    
    for plant in plants:
        for i, customer in enumerate(customers):
            # Truck routes
            distance = base_distances[i] + (hash(plant) % 50)  # Add some variation
            routes_data.append({
                "origin_plant_id": plant,
                "destination_node_id": customer,
                "transport_mode": "truck",
                "distance_km": distance,
                "cost_per_tonne": 8.5 + (hash(f"{plant}{customer}") % 20) / 10,  # 8.5-10.5 per tonne
                "cost_per_tonne_km": 0.05,
                "fixed_cost_per_trip": 500.0,
                "vehicle_capacity_tonnes": 25,
                "min_batch_quantity_tonnes": 500,
                "lead_time_days": distance / 1200,  # ~50 km/h average, 24h/day
                "is_active": "Y",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
    
    for route in routes_data:
        existing = db.query(TransportRoutesModes).filter(
            TransportRoutesModes.origin_plant_id == route["origin_plant_id"],
            TransportRoutesModes.destination_node_id == route["destination_node_id"],
            TransportRoutesModes.transport_mode == route["transport_mode"]
        ).first()
        if not existing:
            route_obj = TransportRoutesModes(**route)
            db.add(route_obj)
    
    db.commit()
    logger.info(f"✅ Loaded {len(routes_data)} transport routes")

def load_safety_stock_data(db: Session):
    """Load safety stock policies"""
    logger.info("Loading safety stock data...")
    
    customers = ["CUST_001", "CUST_002", "CUST_003", "CUST_004", "CUST_005", "CUST_006", "CUST_007"]
    safety_stock_data = []
    
    for customer in customers:
        safety_stock_data.append({
            "node_id": customer,
            "policy_type": "absolute",
            "policy_value": 1500 + (hash(customer) % 1000),  # 1500-2500 tonnes
            "safety_stock_tonnes": 1500 + (hash(customer) % 1000),
            "location_id": customer,
            "product_type": "clinker",
            "penalty_cost_per_tonne": 1000.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
    
    for safety_stock in safety_stock_data:
        existing = db.query(SafetyStockPolicy).filter(
            SafetyStockPolicy.node_id == safety_stock["node_id"]
        ).first()
        if not existing:
            safety_obj = SafetyStockPolicy(**safety_stock)
            db.add(safety_obj)
    
    db.commit()
    logger.info(f"✅ Loaded {len(safety_stock_data)} safety stock policies")

def load_initial_inventory_data(db: Session):
    """Load initial inventory data"""
    logger.info("Loading initial inventory data...")
    
    customers = ["CUST_001", "CUST_002", "CUST_003", "CUST_004", "CUST_005", "CUST_006", "CUST_007"]
    inventory_data = []
    
    for customer in customers:
        inventory_data.append({
            "node_id": customer,
            "period": "2024-01",
            "inventory_tonnes": 2000 + (hash(customer) % 1500),  # 2000-3500 tonnes
            "location_id": customer,
            "product_type": "clinker",
            "initial_stock_tonnes": 2000 + (hash(customer) % 1500),
            "unit_cost": 2800.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
    
    for inventory in inventory_data:
        existing = db.query(InitialInventory).filter(
            InitialInventory.node_id == inventory["node_id"],
            InitialInventory.period == inventory["period"]
        ).first()
        if not existing:
            inventory_obj = InitialInventory(**inventory)
            db.add(inventory_obj)
    
    db.commit()
    logger.info(f"✅ Loaded {len(inventory_data)} inventory records")

def create_sample_optimization_runs(db: Session):
    """Create sample optimization runs and results"""
    logger.info("Creating sample optimization runs...")
    
    scenarios = [
        {
            "name": "base",
            "display_name": "Base Scenario",
            "description": "Baseline scenario with normal demand and capacity"
        },
        {
            "name": "high_demand", 
            "display_name": "High Demand",
            "description": "High demand scenario (25% increase)"
        },
        {
            "name": "low_demand",
            "display_name": "Low Demand", 
            "description": "Low demand scenario (20% decrease)"
        },
        {
            "name": "capacity_constrained",
            "display_name": "Capacity Constrained",
            "description": "Reduced capacity scenario (15% decrease)"
        },
        {
            "name": "transport_disruption",
            "display_name": "Transport Disruption",
            "description": "Transport disruption scenario (35% cost increase)"
        }
    ]
    
    # Create scenario metadata
    for scenario in scenarios:
        existing = db.query(ScenarioMetadata).filter(ScenarioMetadata.scenario_name == scenario["name"]).first()
        if not existing:
            scenario_obj = ScenarioMetadata(
                scenario_name=scenario["name"],
                description=scenario["description"],
                status="completed",
                created_by="system",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(scenario_obj)
    
    # Create optimization runs
    cost_multipliers = [1.0, 1.25, 0.8, 1.15, 1.35]
    base_cost = 1523456.78
    
    for i, scenario in enumerate(scenarios):
        run_id = f"run_{scenario['name']}_{datetime.now().strftime('%Y%m%d')}"
        
        existing_run = db.query(OptimizationRun).filter(OptimizationRun.run_id == run_id).first()
        if not existing_run:
            # Create optimization run
            opt_run = OptimizationRun(
                run_id=run_id,
                scenario_name=scenario["name"],
                status="completed",
                solver_name="HiGHS",
                solver_status="optimal",
                objective_value=base_cost * cost_multipliers[i],
                solve_time_seconds=45.2 + i * 5,
                started_at=datetime.now() - timedelta(hours=i+1),
                completed_at=datetime.now() - timedelta(hours=i),
                validation_passed=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(opt_run)
            
            # Create optimization results
            total_cost = base_cost * cost_multipliers[i]
            opt_results = OptimizationResults(
                run_id=run_id,
                total_cost=total_cost,
                production_cost=total_cost * 0.55,
                transport_cost=total_cost * 0.28,
                inventory_cost=total_cost * 0.12,
                penalty_cost=total_cost * 0.05,
                service_level=0.94 + (i * 0.01),
                demand_fulfillment={"total_fulfilled": 87500 * (0.9 + i * 0.02)},
                production_plan={"PLANT_001": 28500, "PLANT_002": 24800, "PLANT_003": 26200},
                shipment_plan={"PLANT_001-CUST_001": 15000, "PLANT_002-CUST_002": 12000},
                inventory_profile={"CUST_001": 2800, "CUST_002": 1650, "CUST_003": 1200},
                production_utilization={"PLANT_001": 0.95, "PLANT_002": 0.89, "PLANT_003": 0.97},
                stockout_events=2 if i > 2 else 0,
                capacity_violations={},
                created_at=datetime.now()
            )
            db.add(opt_results)
            
            # Create KPI snapshot
            kpi_snapshot = KPISnapshot(
                run_id=run_id,
                scenario_name=scenario["name"],
                total_cost=total_cost,
                cost_per_tonne=total_cost / 79500,
                cost_breakdown={
                    "production_cost": total_cost * 0.55,
                    "transport_cost": total_cost * 0.28,
                    "fixed_trip_cost": total_cost * 0.08,
                    "holding_cost": total_cost * 0.04,
                    "penalty_cost": total_cost * 0.05
                },
                total_production=79500,
                service_level=0.94 + (i * 0.01),
                demand_fulfillment_rate=0.96 - (i * 0.005),
                on_time_delivery_rate=0.92 + (i * 0.01),
                transport_efficiency=0.87 + (i * 0.02),
                inventory_turns=29.2 - (i * 1.5),
                capacity_utilization=0.94 - (i * 0.01),
                sbq_compliance_rate=0.95 - (i * 0.02),
                safety_stock_compliance=0.94 + (i * 0.01),
                kpi_details={
                    "scenario_name": scenario["name"],
                    "run_id": run_id,
                    "timestamp": datetime.now().isoformat(),
                    "status": "completed",
                    "total_cost": total_cost,
                    "production_utilization": [
                        {"plant_name": "Ambuja Cement - Dadri", "plant_id": "PLANT_001", "utilization_pct": 0.95},
                        {"plant_name": "ACC Cement - Wadi", "plant_id": "PLANT_002", "utilization_pct": 0.89},
                        {"plant_name": "Ambuja Cement - Ropar", "plant_id": "PLANT_003", "utilization_pct": 0.97}
                    ],
                    "transport_utilization": [
                        {"from": "PLANT_001", "to": "CUST_001", "mode": "truck", "trips": 45, "capacity_used_pct": 0.87, "sbq_compliance": "Yes"},
                        {"from": "PLANT_002", "to": "CUST_002", "mode": "truck", "trips": 38, "capacity_used_pct": 0.92, "sbq_compliance": "Yes"},
                        {"from": "PLANT_003", "to": "CUST_003", "mode": "truck", "trips": 42, "capacity_used_pct": 0.85, "sbq_compliance": "No" if i > 2 else "Yes"}
                    ],
                    "service_performance": {
                        "demand_fulfillment_rate": 0.96 - (i * 0.005),
                        "on_time_delivery": 0.92 + (i * 0.01),
                        "service_level": 0.94 + (i * 0.01),
                        "stockout_triggered": i > 2
                    },
                    "inventory_metrics": {
                        "safety_stock_compliance": 0.94 + (i * 0.01),
                        "inventory_turns": 29.2 - (i * 1.5),
                        "stockout_events": 2 if i > 2 else 0
                    }
                },
                snapshot_timestamp=datetime.now(),
                created_at=datetime.now()
            )
            db.add(kpi_snapshot)
    
    db.commit()
    logger.info(f"✅ Created {len(scenarios)} optimization runs with results and KPI snapshots")

def main():
    """Main ETL pipeline"""
    logger.info("🚀 Starting Production Database ETL Pipeline")
    
    # Create all tables
    create_all_tables()
    
    # Load data
    db = SessionLocal()
    try:
        load_plant_master_data(db)
        load_production_capacity_data(db)
        load_demand_forecast_data(db)
        load_transport_routes_data(db)
        load_safety_stock_data(db)
        load_initial_inventory_data(db)
        create_sample_optimization_runs(db)
        
        logger.info("🎉 ETL Pipeline completed successfully!")
        logger.info("📊 Database is now ready for production use")
        
        # Verify data
        plant_count = db.query(PlantMaster).count()
        demand_count = db.query(DemandForecast).count()
        route_count = db.query(TransportRoutesModes).count()
        run_count = db.query(OptimizationRun).count()
        kpi_count = db.query(KPISnapshot).count()
        
        logger.info(f"📈 Data Summary:")
        logger.info(f"   - Plants: {plant_count}")
        logger.info(f"   - Demand Records: {demand_count}")
        logger.info(f"   - Transport Routes: {route_count}")
        logger.info(f"   - Optimization Runs: {run_count}")
        logger.info(f"   - KPI Snapshots: {kpi_count}")
        
    except Exception as e:
        logger.error(f"❌ ETL Pipeline failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()