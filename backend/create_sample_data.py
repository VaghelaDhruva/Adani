"""
Create sample data for the Clinker Supply Chain Optimization System
"""

import os
import sys
from pathlib import Path

# Add the backend app to the path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Set environment variables
os.environ["DATABASE_URL"] = "sqlite:///./clinker_supply_chain.db"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["BROKER_URL"] = "redis://localhost:6379"
os.environ["RESULT_BACKEND"] = "redis://localhost:6379"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.models.plant_master import PlantMaster
from app.db.models.production_capacity_cost import ProductionCapacityCost
from app.db.models.transport_routes_modes import TransportRoutesModes
from app.db.models.demand_forecast import DemandForecast
from app.db.models.initial_inventory import InitialInventory
from app.db.models.safety_stock_policy import SafetyStockPolicy
from app.core.config import get_settings

def create_sample_data():
    """Create sample data for demonstration."""
    
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Clear existing data
        db.query(SafetyStockPolicy).delete()
        db.query(InitialInventory).delete()
        db.query(DemandForecast).delete()
        db.query(TransportRoutesModes).delete()
        db.query(ProductionCapacityCost).delete()
        db.query(PlantMaster).delete()
        
        # Create Plants
        plants = [
            PlantMaster(
                plant_id="PLANT_MUM",
                plant_name="Mumbai Clinker Plant",
                plant_type="clinker",
                latitude=19.0760,
                longitude=72.8777,
                region="West",
                country="India"
            ),
            PlantMaster(
                plant_id="PLANT_DEL",
                plant_name="Delhi Grinding Unit",
                plant_type="grinding",
                latitude=28.7041,
                longitude=77.1025,
                region="North",
                country="India"
            ),
            PlantMaster(
                plant_id="PLANT_CHE",
                plant_name="Chennai Terminal",
                plant_type="terminal",
                latitude=13.0827,
                longitude=80.2707,
                region="South",
                country="India"
            ),
            PlantMaster(
                plant_id="PLANT_KOL",
                plant_name="Kolkata Plant",
                plant_type="clinker",
                latitude=22.5726,
                longitude=88.3639,
                region="East",
                country="India"
            )
        ]
        
        for plant in plants:
            db.add(plant)
        
        # Create Production Capacity
        periods = ["2025-01", "2025-02", "2025-03", "2025-04"]
        production_data = [
            # Mumbai Plant
            {"plant_id": "PLANT_MUM", "capacity": 50000, "cost": 2500},
            {"plant_id": "PLANT_DEL", "capacity": 30000, "cost": 2800},
            {"plant_id": "PLANT_CHE", "capacity": 25000, "cost": 2600},
            {"plant_id": "PLANT_KOL", "capacity": 40000, "cost": 2400}
        ]
        
        for period in periods:
            for prod in production_data:
                capacity = ProductionCapacityCost(
                    plant_id=prod["plant_id"],
                    period=period,
                    max_capacity_tonnes=prod["capacity"],
                    variable_cost_per_tonne=prod["cost"],
                    fixed_cost_per_period=500000,
                    min_run_level=0.3 * prod["capacity"]
                )
                db.add(capacity)
        
        # Create Transport Routes
        routes = [
            # From Mumbai
            {"origin": "PLANT_MUM", "dest": "CUST_MUM_001", "mode": "road", "distance": 50, "cost_per_tonne": 150, "capacity": 25},
            {"origin": "PLANT_MUM", "dest": "CUST_MUM_002", "mode": "road", "distance": 75, "cost_per_tonne": 180, "capacity": 25},
            {"origin": "PLANT_MUM", "dest": "CUST_PUN_001", "mode": "road", "distance": 150, "cost_per_tonne": 300, "capacity": 30},
            
            # From Delhi
            {"origin": "PLANT_DEL", "dest": "CUST_DEL_001", "mode": "road", "distance": 40, "cost_per_tonne": 120, "capacity": 25},
            {"origin": "PLANT_DEL", "dest": "CUST_DEL_002", "mode": "road", "distance": 60, "cost_per_tonne": 160, "capacity": 25},
            {"origin": "PLANT_DEL", "dest": "CUST_GUR_001", "mode": "road", "distance": 80, "cost_per_tonne": 200, "capacity": 30},
            
            # From Chennai
            {"origin": "PLANT_CHE", "dest": "CUST_CHE_001", "mode": "road", "distance": 45, "cost_per_tonne": 140, "capacity": 25},
            {"origin": "PLANT_CHE", "dest": "CUST_CHE_002", "mode": "road", "distance": 70, "cost_per_tonne": 170, "capacity": 25},
            {"origin": "PLANT_CHE", "dest": "CUST_BAN_001", "mode": "road", "distance": 350, "cost_per_tonne": 600, "capacity": 35},
            
            # From Kolkata
            {"origin": "PLANT_KOL", "dest": "CUST_KOL_001", "mode": "road", "distance": 35, "cost_per_tonne": 110, "capacity": 25},
            {"origin": "PLANT_KOL", "dest": "CUST_KOL_002", "mode": "road", "distance": 55, "cost_per_tonne": 150, "capacity": 25},
            
            # Inter-plant transfers
            {"origin": "PLANT_MUM", "dest": "PLANT_DEL", "mode": "rail", "distance": 1400, "cost_per_tonne": 800, "capacity": 50},
            {"origin": "PLANT_KOL", "dest": "PLANT_CHE", "mode": "rail", "distance": 1600, "cost_per_tonne": 900, "capacity": 50}
        ]
        
        for route in routes:
            transport = TransportRoutesModes(
                origin_plant_id=route["origin"],
                destination_node_id=route["dest"],
                transport_mode=route["mode"],
                distance_km=route["distance"],
                cost_per_tonne=route["cost_per_tonne"],
                cost_per_tonne_km=route["cost_per_tonne"] / route["distance"],
                fixed_cost_per_trip=2000 if route["mode"] == "rail" else 500,
                vehicle_capacity_tonnes=route["capacity"],
                min_batch_quantity_tonnes=5,
                lead_time_days=3 if route["mode"] == "rail" else 1,
                is_active="Y"
            )
            db.add(transport)
        
        # Create Demand Forecast
        customers = [
            "CUST_MUM_001", "CUST_MUM_002", "CUST_PUN_001",
            "CUST_DEL_001", "CUST_DEL_002", "CUST_GUR_001",
            "CUST_CHE_001", "CUST_CHE_002", "CUST_BAN_001",
            "CUST_KOL_001", "CUST_KOL_002"
        ]
        
        base_demands = {
            "CUST_MUM_001": 8000, "CUST_MUM_002": 6000, "CUST_PUN_001": 12000,
            "CUST_DEL_001": 7000, "CUST_DEL_002": 5000, "CUST_GUR_001": 9000,
            "CUST_CHE_001": 6500, "CUST_CHE_002": 4500, "CUST_BAN_001": 15000,
            "CUST_KOL_001": 8500, "CUST_KOL_002": 7500
        }
        
        for period in periods:
            for customer in customers:
                base_demand = base_demands[customer]
                # Add some seasonal variation
                seasonal_factor = 1.1 if period in ["2025-01", "2025-04"] else 0.95
                demand = base_demand * seasonal_factor
                
                forecast = DemandForecast(
                    customer_node_id=customer,
                    period=period,
                    demand_tonnes=demand,
                    demand_low_tonnes=demand * 0.9,
                    demand_high_tonnes=demand * 1.1,
                    confidence_level=0.85,
                    source="forecast_model"
                )
                db.add(forecast)
        
        # Create Initial Inventory
        for plant_id in ["PLANT_MUM", "PLANT_DEL", "PLANT_CHE", "PLANT_KOL"]:
            inventory = InitialInventory(
                node_id=plant_id,
                period="2025-01",
                inventory_tonnes=5000  # 5000 tonnes initial inventory
            )
            db.add(inventory)
        
        # Create Safety Stock Policy
        safety_policies = [
            {"node_id": "PLANT_MUM", "policy_type": "days_of_cover", "policy_value": 7, "safety_stock": 3500},
            {"node_id": "PLANT_DEL", "policy_type": "days_of_cover", "policy_value": 5, "safety_stock": 2500},
            {"node_id": "PLANT_CHE", "policy_type": "days_of_cover", "policy_value": 6, "safety_stock": 3000},
            {"node_id": "PLANT_KOL", "policy_type": "days_of_cover", "policy_value": 7, "safety_stock": 3200}
        ]
        
        for policy in safety_policies:
            safety_stock = SafetyStockPolicy(
                node_id=policy["node_id"],
                policy_type=policy["policy_type"],
                policy_value=policy["policy_value"],
                safety_stock_tonnes=policy["safety_stock"],
                max_inventory_tonnes=policy["safety_stock"] * 3
            )
            db.add(safety_stock)
        
        # Commit all changes
        db.commit()
        print("✅ Sample data created successfully!")
        print(f"Created:")
        print(f"  - {len(plants)} plants")
        print(f"  - {len(plants) * len(periods)} production capacity records")
        print(f"  - {len(routes)} transport routes")
        print(f"  - {len(customers) * len(periods)} demand forecasts")
        print(f"  - {len(plants)} initial inventory records")
        print(f"  - {len(safety_policies)} safety stock policies")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()