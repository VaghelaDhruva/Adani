#!/usr/bin/env python3
"""
Load sample data for testing the optimization system.
"""

from sqlalchemy.orm import sessionmaker
from app.db.session import engine
from app.db.models.plant_master import PlantMaster
from app.db.models.production_capacity_cost import ProductionCapacityCost
from app.db.models.transport_routes_modes import TransportRoutesModes
from app.db.models.demand_forecast import DemandForecast
from app.db.models.initial_inventory import InitialInventory
from app.db.models.safety_stock_policy import SafetyStockPolicy

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def load_sample_data():
    """Load sample data for testing."""
    
    db = SessionLocal()
    
    try:
        # Clear existing data
        db.query(SafetyStockPolicy).delete()
        db.query(InitialInventory).delete()
        db.query(DemandForecast).delete()
        db.query(TransportRoutesModes).delete()
        db.query(ProductionCapacityCost).delete()
        db.query(PlantMaster).delete()
        
        # Load plant master data
        plants = [
            PlantMaster(
                plant_id="PLANT_001",
                plant_name="Mumbai Clinker Plant",
                plant_type="clinker",
                latitude=19.0760,
                longitude=72.8777,
                region="West",
                country="India"
            ),
            PlantMaster(
                plant_id="PLANT_002",
                plant_name="Delhi Grinding Unit",
                plant_type="grinding",
                latitude=28.7041,
                longitude=77.1025,
                region="North",
                country="India"
            ),
            PlantMaster(
                plant_id="PLANT_003",
                plant_name="Chennai Terminal",
                plant_type="terminal",
                latitude=13.0827,
                longitude=80.2707,
                region="South",
                country="India"
            )
        ]
        
        for plant in plants:
            db.add(plant)
        
        # Load production capacity data
        periods = ["2025-01", "2025-02", "2025-03"]
        capacities = [
            ("PLANT_001", 100000, 1850),  # Mumbai - high capacity, high cost
            ("PLANT_002", 75000, 1750),   # Delhi - medium capacity, medium cost
            ("PLANT_003", 60000, 1650)    # Chennai - lower capacity, lower cost
        ]
        
        for plant_id, capacity, cost in capacities:
            for period in periods:
                prod_capacity = ProductionCapacityCost(
                    plant_id=plant_id,
                    period=period,
                    max_capacity_tonnes=capacity,
                    variable_cost_per_tonne=cost,
                    fixed_cost_per_period=50000,
                    min_run_level=0.3,
                    holding_cost_per_tonne=10.0
                )
                db.add(prod_capacity)
        
        # Load transport routes
        routes = [
            # From Mumbai
            ("PLANT_001", "CUST_001", "road", 150, 120, 0, 2500, 25, 1.5),
            ("PLANT_001", "CUST_002", "rail", 300, 80, 0, 5000, 50, 2.0),
            ("PLANT_001", "CUST_003", "road", 200, 130, 0, 2500, 25, 1.8),
            
            # From Delhi
            ("PLANT_002", "CUST_004", "road", 100, 110, 0, 2500, 25, 1.2),
            ("PLANT_002", "CUST_005", "rail", 250, 75, 0, 5000, 50, 1.8),
            ("PLANT_002", "CUST_001", "road", 400, 140, 0, 2500, 25, 2.5),
            
            # From Chennai
            ("PLANT_003", "CUST_006", "road", 120, 115, 0, 2500, 25, 1.3),
            ("PLANT_003", "CUST_007", "road", 180, 125, 0, 2500, 25, 1.6),
            ("PLANT_003", "CUST_002", "rail", 350, 85, 0, 5000, 50, 2.2)
        ]
        
        for origin, dest, mode, distance, cost_per_tonne, cost_per_km, fixed_cost, capacity, lead_time in routes:
            route = TransportRoutesModes(
                origin_plant_id=origin,
                destination_node_id=dest,
                transport_mode=mode,
                distance_km=distance,
                cost_per_tonne=cost_per_tonne,
                cost_per_tonne_km=cost_per_km,
                fixed_cost_per_trip=fixed_cost,
                vehicle_capacity_tonnes=capacity * 100,  # Convert to tonnes
                min_batch_quantity_tonnes=500,
                lead_time_days=lead_time,
                is_active="Y"
            )
            db.add(route)
        
        # Load demand forecast
        customers = ["CUST_001", "CUST_002", "CUST_003", "CUST_004", "CUST_005", "CUST_006", "CUST_007"]
        base_demands = [15000, 12000, 18000, 20000, 14000, 16000, 13000]
        
        for i, customer in enumerate(customers):
            for period in periods:
                # Add some variation by period
                period_multiplier = {"2025-01": 1.0, "2025-02": 1.1, "2025-03": 0.95}[period]
                demand = base_demands[i] * period_multiplier
                
                demand_forecast = DemandForecast(
                    customer_node_id=customer,
                    period=period,
                    demand_tonnes=demand,
                    demand_low_tonnes=demand * 0.9,
                    demand_high_tonnes=demand * 1.1,
                    confidence_level=0.95,
                    source="forecast_model"
                )
                db.add(demand_forecast)
        
        # Load initial inventory
        all_locations = [p.plant_id for p in plants] + customers
        for location in all_locations:
            inventory = InitialInventory(
                location_id=location,
                product_type="clinker",
                initial_stock_tonnes=1000,  # 1000 tonnes initial stock
                unit_cost=1800
            )
            db.add(inventory)
        
        # Load safety stock policies
        for location in all_locations:
            safety_stock = SafetyStockPolicy(
                location_id=location,
                product_type="clinker",
                safety_stock_tonnes=500,  # 500 tonnes safety stock
                safety_stock_days=3,
                penalty_cost_per_tonne=2000  # High penalty for stockouts
            )
            db.add(safety_stock)
        
        db.commit()
        print("Sample data loaded successfully!")
        
        # Print summary
        print(f"Loaded {len(plants)} plants")
        print(f"Loaded {len(capacities) * len(periods)} production capacity records")
        print(f"Loaded {len(routes)} transport routes")
        print(f"Loaded {len(customers) * len(periods)} demand forecasts")
        print(f"Loaded {len(all_locations)} initial inventory records")
        print(f"Loaded {len(all_locations)} safety stock policies")
        
    except Exception as e:
        print(f"Error loading sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    load_sample_data()