#!/usr/bin/env python3
"""
CSV Data Integration Script for Clinker Supply Chain System
Integrates real CSV data with smart fallbacks for missing fields.
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta
import numpy as np

def create_integrated_database():
    """Create new database with integrated CSV data and smart fallbacks."""
    
    # Database setup
    db_path = "./clinker_supply_chain_integrated.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🚀 Starting CSV Data Integration...")
    
    # Create tables
    create_tables(cursor)
    
    # Process each CSV file
    process_plants_data(cursor)
    process_demand_data(cursor)
    process_transportation_data(cursor)
    process_inventory_data(cursor)
    process_schedule_data(cursor)
    
    conn.commit()
    conn.close()
    
    print("✅ CSV Data Integration Complete!")
    print(f"📁 New database created: {db_path}")
    
    return db_path

def create_tables(cursor):
    """Create all required database tables."""
    
    # Plant Master Table
    cursor.execute("""
        CREATE TABLE plant_master (
            plant_id TEXT PRIMARY KEY,
            plant_name TEXT,
            company_name TEXT,
            location_name TEXT,
            plant_type TEXT,
            state_name TEXT,
            latitude REAL,
            longitude REAL,
            region TEXT,
            country TEXT
        )
    """)
    
    # Production Capacity Cost Table
    cursor.execute("""
        CREATE TABLE production_capacity_cost (
            plant_id TEXT,
            period TEXT,
            max_capacity_tonnes REAL,
            daily_capacity_tonnes REAL,
            variable_cost_per_tonne REAL,
            fixed_cost_per_period REAL,
            min_run_level REAL,
            PRIMARY KEY (plant_id, period)
        )
    """)
    
    # Transport Routes Modes Table
    cursor.execute("""
        CREATE TABLE transport_routes_modes (
            origin_plant_id TEXT,
            destination_node_id TEXT,
            transport_mode TEXT,
            distance_km REAL,
            cost_per_tonne REAL,
            cost_per_tonne_km REAL,
            fixed_cost_per_trip REAL,
            vehicle_capacity_tonnes REAL,
            min_batch_quantity_tonnes REAL,
            lead_time_days INTEGER,
            is_active TEXT,
            rail_feasible TEXT,
            PRIMARY KEY (origin_plant_id, destination_node_id, transport_mode)
        )
    """)
    
    # Demand Forecast Table
    cursor.execute("""
        CREATE TABLE demand_forecast (
            customer_node_id TEXT,
            period TEXT,
            demand_tonnes REAL,
            demand_low_tonnes REAL,
            demand_high_tonnes REAL,
            confidence_level REAL,
            source TEXT,
            PRIMARY KEY (customer_node_id, period)
        )
    """)
    
    # Inventory Levels Table
    cursor.execute("""
        CREATE TABLE inventory_levels (
            plant_id TEXT,
            date TEXT,
            inventory_mt REAL,
            safety_stock_mt REAL,
            max_capacity_mt REAL,
            utilization_pct REAL,
            PRIMARY KEY (plant_id, date)
        )
    """)
    
    # Transportation Schedule Table
    cursor.execute("""
        CREATE TABLE transportation_schedule (
            date TEXT,
            source_plant_id TEXT,
            destination_plant_id TEXT,
            transport_mode TEXT,
            quantity_mt REAL,
            num_trips REAL,
            cost_inr REAL,
            PRIMARY KEY (date, source_plant_id, destination_plant_id, transport_mode)
        )
    """)
    
    print("📋 Database tables created successfully")

def process_plants_data(cursor):
    """Process plants.csv with geographic and capacity data."""
    
    print("🏭 Processing plants data...")
    
    # Read plants CSV
    plants_df = pd.read_csv('Data/plants.csv')
    
    # Region mapping based on states
    region_mapping = {
        'Chhattisgarh': 'Central', 'Madhya Pradesh': 'Central', 'Maharashtra': 'West',
        'Karnataka': 'South', 'Himachal Pradesh': 'North', 'Jharkhand': 'East',
        'Odisha': 'East', 'West Bengal': 'East', 'Rajasthan': 'North',
        'Tamil Nadu': 'South', 'Gujarat': 'West', 'Andhra Pradesh': 'South',
        'Telangana': 'South', 'Uttar Pradesh': 'North', 'Uttarakhand': 'North',
        'Punjab': 'North', 'Kerala': 'South'
    }
    
    # Insert plant master data
    for _, row in plants_df.iterrows():
        region = region_mapping.get(row['STATE_NAME'], 'Unknown')
        
        cursor.execute("""
            INSERT INTO plant_master VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row['PLANT_ID'],
            row['LOCATION_NAME'],
            row['COMPANY_NAME'],
            row['LOCATION_NAME'],
            row['PLANT_TYPE'],
            row['STATE_NAME'],
            row['LATITUDE'],
            row['LONGITUDE'],
            region,
            'India'
        ))
    
    # Generate production capacity data for 2025-01 period
    for _, row in plants_df.iterrows():
        # Convert daily to monthly capacity (assuming 30 days)
        monthly_capacity = row['PROD_CAPACITY_MT_DAY'] * 30
        
        # Realistic variable costs based on plant type
        if row['PLANT_TYPE'] == 'IU':  # Integrated Units (clinker production)
            var_cost = np.random.uniform(2400, 2800)  # ₹2400-2800 per tonne
            fixed_cost = monthly_capacity * 100  # ₹100 per tonne capacity
        else:  # GU - Grinding Units (cement production)
            var_cost = np.random.uniform(1800, 2200)  # Lower for grinding
            fixed_cost = monthly_capacity * 80   # Lower fixed costs
        
        cursor.execute("""
            INSERT INTO production_capacity_cost VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            row['PLANT_ID'],
            '2025-01',
            monthly_capacity,
            row['PROD_CAPACITY_MT_DAY'],
            var_cost,
            fixed_cost,
            monthly_capacity * 0.3  # 30% minimum run level
        ))
    
    print(f"✅ Processed {len(plants_df)} plants with production capacity data")

def process_demand_data(cursor):
    """Process demand.csv and generate monthly forecasts."""
    
    print("📊 Processing demand data...")
    
    # Read demand CSV
    demand_df = pd.read_csv('Data/demand.csv')
    
    # Convert single day demand to monthly forecast
    for _, row in demand_df.iterrows():
        daily_demand = row['Demand']
        monthly_demand = daily_demand * 30  # Scale to monthly
        
        # Add realistic variance for forecast ranges
        low_demand = monthly_demand * 0.9   # 10% lower
        high_demand = monthly_demand * 1.1  # 10% higher
        
        cursor.execute("""
            INSERT INTO demand_forecast VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            row['plant_Id'],  # Using plant as customer node
            '2025-01',
            monthly_demand,
            low_demand,
            high_demand,
            0.85,  # 85% confidence
            'csv_forecast'
        ))
    
    print(f"✅ Processed {len(demand_df)} demand forecasts")

def process_transportation_data(cursor):
    """Process transportation.csv with costs and routes."""
    
    print("🚛 Processing transportation data...")
    
    # Read transportation CSV
    transport_df = pd.read_csv('Data/transportation.csv')
    
    # Process each route
    for _, row in transport_df.iterrows():
        # Determine if rail is feasible
        rail_feasible = 'Y' if row['rail_feasible'] else 'N'
        
        # Road transport data
        if pd.notna(row['road_cost_1_quantity']):
            # Estimate distance (cost/20 as rough approximation)
            estimated_distance = max(10, row['road_cost_1_quantity'] / 20)
            
            cursor.execute("""
                INSERT OR REPLACE INTO transport_routes_modes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['source'],
                row['destination'],
                'road',
                estimated_distance,
                row['road_cost_1_quantity'],
                row['road_cost_1_quantity'] / estimated_distance,
                4000,  # Standard ₹4000 per trip
                25,    # 25 tonne truck capacity
                5,     # 5 tonne minimum batch
                2,     # 2 days lead time
                'Y',   # Active
                'N/A'  # Not applicable for road
            ))
        
        # Rail transport data
        if pd.notna(row['rail_cost_1_quantity']) and rail_feasible == 'Y':
            # Estimate distance for rail (typically longer routes)
            estimated_distance = max(50, row['rail_cost_1_quantity'] / 5)
            
            cursor.execute("""
                INSERT OR REPLACE INTO transport_routes_modes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['source'],
                row['destination'],
                'rail',
                estimated_distance,
                row['rail_cost_1_quantity'],
                row['rail_cost_1_quantity'] / estimated_distance,
                15000,  # Higher fixed cost for rail
                1000,   # 1000 tonne rail capacity
                100,    # 100 tonne minimum batch
                5,      # 5 days lead time
                'Y',    # Active
                rail_feasible
            ))
    
    print(f"✅ Processed {len(transport_df)} transportation routes")

def process_inventory_data(cursor):
    """Process inventory_levels.csv with time series data."""
    
    print("📦 Processing inventory data...")
    
    # Read first 1000 rows to get sample (file is very large)
    inventory_df = pd.read_csv('Data/inventory_levels.csv', nrows=1000)
    
    # Insert inventory data
    for _, row in inventory_df.iterrows():
        cursor.execute("""
            INSERT OR REPLACE INTO inventory_levels VALUES (?, ?, ?, ?, ?, ?)
        """, (
            row['Plant_ID'],
            row['Date'],
            row['Inventory_MT'],
            row['Safety_Stock_MT'],
            row['Max_Capacity_MT'],
            row['Utilization_Pct']
        ))
    
    print(f"✅ Processed {len(inventory_df)} inventory records")

def process_schedule_data(cursor):
    """Process transportation_schedule.csv with active shipments."""
    
    print("🚚 Processing transportation schedule...")
    
    # Read schedule CSV
    schedule_df = pd.read_csv('Data/transportation_schedule.csv')
    
    # Insert schedule data
    for _, row in schedule_df.iterrows():
        cursor.execute("""
            INSERT INTO transportation_schedule VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            row['Date'],
            row['Source'],
            row['Destination'],
            row['Mode'],
            row['Quantity_MT'],
            row['Num_Trips'],
            row['Cost_INR']
        ))
    
    print(f"✅ Processed {len(schedule_df)} transportation schedules")

def generate_summary_report(db_path):
    """Generate summary report of integrated data."""
    
    conn = sqlite3.connect(db_path)
    
    print("\n📈 INTEGRATED DATA SUMMARY REPORT")
    print("=" * 50)
    
    # Plants summary
    plants_count = pd.read_sql("SELECT COUNT(*) as count FROM plant_master", conn).iloc[0]['count']
    iu_count = pd.read_sql("SELECT COUNT(*) as count FROM plant_master WHERE plant_type='IU'", conn).iloc[0]['count']
    gu_count = pd.read_sql("SELECT COUNT(*) as count FROM plant_master WHERE plant_type='GU'", conn).iloc[0]['count']
    
    print(f"🏭 PLANTS: {plants_count} total ({iu_count} IU + {gu_count} GU)")
    
    # Capacity summary
    capacity_df = pd.read_sql("SELECT SUM(max_capacity_tonnes) as total FROM production_capacity_cost", conn)
    total_capacity = capacity_df.iloc[0]['total']
    print(f"⚙️  TOTAL CAPACITY: {total_capacity:,.0f} tonnes/month")
    
    # Demand summary
    demand_df = pd.read_sql("SELECT SUM(demand_tonnes) as total FROM demand_forecast", conn)
    total_demand = demand_df.iloc[0]['total']
    print(f"📊 TOTAL DEMAND: {total_demand:,.0f} tonnes/month")
    
    # Utilization
    utilization = (total_demand / total_capacity) * 100
    print(f"📈 CAPACITY UTILIZATION: {utilization:.1f}%")
    
    # Transport routes
    routes_count = pd.read_sql("SELECT COUNT(*) as count FROM transport_routes_modes", conn).iloc[0]['count']
    print(f"🚛 TRANSPORT ROUTES: {routes_count:,}")
    
    # Cost analysis
    cost_df = pd.read_sql("""
        SELECT 
            transport_mode,
            COUNT(*) as routes,
            AVG(cost_per_tonne) as avg_cost,
            MIN(cost_per_tonne) as min_cost,
            MAX(cost_per_tonne) as max_cost
        FROM transport_routes_modes 
        GROUP BY transport_mode
    """, conn)
    
    print("\n💰 TRANSPORT COST ANALYSIS:")
    for _, row in cost_df.iterrows():
        print(f"   {row['transport_mode'].upper()}: {row['routes']} routes, ₹{row['avg_cost']:.0f}/tonne avg (₹{row['min_cost']:.0f}-₹{row['max_cost']:.0f})")
    
    # Geographic distribution
    region_df = pd.read_sql("""
        SELECT region, COUNT(*) as plants 
        FROM plant_master 
        GROUP BY region 
        ORDER BY plants DESC
    """, conn)
    
    print("\n🗺️  GEOGRAPHIC DISTRIBUTION:")
    for _, row in region_df.iterrows():
        print(f"   {row['region']}: {row['plants']} plants")
    
    conn.close()

if __name__ == "__main__":
    # Create integrated database
    db_path = create_integrated_database()
    
    # Generate summary report
    generate_summary_report(db_path)
    
    print(f"\n🎯 INTEGRATION COMPLETE!")
    print(f"📁 Database: {db_path}")
    print(f"🔄 Ready to update backend to use integrated data")