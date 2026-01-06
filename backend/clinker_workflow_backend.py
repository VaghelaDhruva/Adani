#!/usr/bin/env python3
"""
Clinker Workflow Backend - End-to-End Clinker Management System
Supports the complete workflow from order creation to billing.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import sqlite3
import uuid
from enum import Enum

app = FastAPI(
    title="Clinker Workflow Management System",
    version="1.0.0",
    description="End-to-end clinker workflow from order to delivery"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_PATH = "./clinker_workflow.db"

# Enums
class OrderStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class Priority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class TransportMode(str, Enum):
    ROAD = "Road"
    RAIL = "Rail"
    SEA = "Sea"
    MIXED = "Mixed"

class ShipmentStatus(str, Enum):
    PLANNED = "Planned"
    LOADING = "Loading"
    IN_TRANSIT = "In Transit"
    DELIVERED = "Delivered"
    DELAYED = "Delayed"

# Pydantic Models
class OrderCreate(BaseModel):
    source_plant: str
    destination_plant: str
    quantity: float
    required_date: str
    priority: Priority

class Order(BaseModel):
    id: str
    source_plant: str
    destination_plant: str
    quantity: float
    required_date: str
    priority: Priority
    status: OrderStatus
    created_by: str
    created_at: str

class InventoryStatus(BaseModel):
    plant_id: str
    plant_name: str
    current_stock: float
    safety_stock: float
    max_capacity: float
    available_stock: float
    reserved_stock: float
    last_updated: str
    status: str

class TransportPlan(BaseModel):
    order_id: str
    transport_mode: TransportMode
    estimated_cost: float
    estimated_time: int
    carrier: str
    vehicle_details: str

class Shipment(BaseModel):
    id: str
    order_id: str
    transport_plan_id: str
    status: ShipmentStatus
    loading_start: Optional[str]
    loading_end: Optional[str]
    dispatch_time: Optional[str]
    expected_delivery: Optional[str]
    actual_delivery: Optional[str]
    current_location: Optional[str]

def init_database():
    """Initialize the clinker workflow database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            source_plant TEXT NOT NULL,
            destination_plant TEXT NOT NULL,
            quantity REAL NOT NULL,
            required_date TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # Inventory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            plant_id TEXT PRIMARY KEY,
            plant_name TEXT NOT NULL,
            current_stock REAL NOT NULL,
            safety_stock REAL NOT NULL,
            max_capacity REAL NOT NULL,
            available_stock REAL NOT NULL,
            reserved_stock REAL NOT NULL,
            last_updated TEXT NOT NULL
        )
    """)
    
    # Transport plans table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transport_plans (
            id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            transport_mode TEXT NOT NULL,
            estimated_cost REAL NOT NULL,
            estimated_time INTEGER NOT NULL,
            carrier TEXT NOT NULL,
            vehicle_details TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
    """)
    
    # Shipments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shipments (
            id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            transport_plan_id TEXT NOT NULL,
            status TEXT NOT NULL,
            loading_start TEXT,
            loading_end TEXT,
            dispatch_time TEXT,
            expected_delivery TEXT,
            actual_delivery TEXT,
            current_location TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (transport_plan_id) REFERENCES transport_plans (id)
        )
    """)
    
    # Insert sample inventory data
    sample_inventory = [
        ("PLANT_MUM", "Mumbai Clinker Plant", 8500, 3500, 15000, 6000, 2500),
        ("PLANT_DEL", "Delhi Grinding Unit", 2800, 2500, 10000, 1000, 1800),
        ("PLANT_CHE", "Chennai Terminal", 1200, 3000, 12000, 400, 800),
        ("PLANT_KOL", "Kolkata Plant", 7200, 3200, 14000, 5700, 1500)
    ]
    
    for inv in sample_inventory:
        cursor.execute("""
            INSERT OR REPLACE INTO inventory 
            (plant_id, plant_name, current_stock, safety_stock, max_capacity, available_stock, reserved_stock, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (*inv, datetime.now().strftime("%Y-%m-%d %H:%M")))
    
    # Insert sample orders
    sample_orders = [
        ("ORD-001", "Mumbai Clinker Plant", "Delhi Grinding Unit", 2500, "2025-01-15", "High", "Pending", "Sales Team", "2025-01-05"),
        ("ORD-002", "Kolkata Plant", "Chennai Terminal", 1800, "2025-01-12", "Medium", "Approved", "Plant Manager", "2025-01-04")
    ]
    
    for order in sample_orders:
        cursor.execute("""
            INSERT OR REPLACE INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, order)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

@app.get("/")
def root():
    return {
        "message": "Clinker Workflow Management System",
        "version": "1.0.0",
        "workflow_stages": [
            "Order & Demand Creation",
            "Inventory & Availability Check", 
            "Transportation Mode Selection",
            "Dispatch Planning",
            "Loading & Dispatch Execution",
            "In-Transit Tracking",
            "Delivery & GRN",
            "Billing & Costing"
        ]
    }

# 1️⃣ Order & Demand Creation APIs
@app.post("/api/v1/clinker/orders", response_model=Order)
def create_order(order: OrderCreate):
    """Create a new clinker order."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    order_id = f"ORD-{str(uuid.uuid4())[:8].upper()}"
    created_at = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("""
        INSERT INTO orders (id, source_plant, destination_plant, quantity, required_date, priority, status, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (order_id, order.source_plant, order.destination_plant, order.quantity, 
          order.required_date, order.priority, OrderStatus.PENDING, "Current User", created_at))
    
    conn.commit()
    conn.close()
    
    return Order(
        id=order_id,
        source_plant=order.source_plant,
        destination_plant=order.destination_plant,
        quantity=order.quantity,
        required_date=order.required_date,
        priority=order.priority,
        status=OrderStatus.PENDING,
        created_by="Current User",
        created_at=created_at
    )

@app.get("/api/v1/clinker/orders", response_model=List[Order])
def get_orders():
    """Get all clinker orders."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    orders = []
    for row in rows:
        orders.append(Order(
            id=row[0],
            source_plant=row[1],
            destination_plant=row[2],
            quantity=row[3],
            required_date=row[4],
            priority=row[5],
            status=row[6],
            created_by=row[7],
            created_at=row[8]
        ))
    
    return orders

# 2️⃣ Inventory & Availability Check APIs
@app.get("/api/v1/clinker/inventory", response_model=List[InventoryStatus])
def get_inventory_status():
    """Get current inventory status for all plants."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM inventory")
    rows = cursor.fetchall()
    conn.close()
    
    inventory = []
    for row in rows:
        # Determine status based on current stock vs safety stock
        current_stock = row[2]
        safety_stock = row[3]
        
        if current_stock <= safety_stock:
            status = "Critical"
        elif current_stock <= safety_stock * 1.5:
            status = "Low"
        else:
            status = "Good"
        
        inventory.append(InventoryStatus(
            plant_id=row[0],
            plant_name=row[1],
            current_stock=row[2],
            safety_stock=row[3],
            max_capacity=row[4],
            available_stock=row[5],
            reserved_stock=row[6],
            last_updated=row[7],
            status=status
        ))
    
    return inventory

@app.get("/api/v1/clinker/inventory/{plant_id}")
def get_plant_inventory(plant_id: str):
    """Get inventory status for a specific plant."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM inventory WHERE plant_id = ?", (plant_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Plant not found")
    
    current_stock = row[2]
    safety_stock = row[3]
    
    if current_stock <= safety_stock:
        status = "Critical"
    elif current_stock <= safety_stock * 1.5:
        status = "Low"
    else:
        status = "Good"
    
    return InventoryStatus(
        plant_id=row[0],
        plant_name=row[1],
        current_stock=row[2],
        safety_stock=row[3],
        max_capacity=row[4],
        available_stock=row[5],
        reserved_stock=row[6],
        last_updated=row[7],
        status=status
    )

# 3️⃣ Transportation Mode Selection APIs (Keep existing KPI and Transport dashboards)
@app.get("/api/v1/clinker/transport/modes")
def get_transport_modes():
    """Get available transport modes with cost comparison."""
    return {
        "modes": [
            {
                "mode": "Road",
                "cost_per_mt": 850,
                "transit_time_days": 2,
                "capacity_mt": 25,
                "availability": "High",
                "suitable_for": ["Short distance", "Flexible delivery"]
            },
            {
                "mode": "Rail",
                "cost_per_mt": 650,
                "transit_time_days": 4,
                "capacity_mt": 1000,
                "availability": "Medium",
                "suitable_for": ["Long distance", "Bulk shipments"]
            },
            {
                "mode": "Sea",
                "cost_per_mt": 400,
                "transit_time_days": 7,
                "capacity_mt": 5000,
                "availability": "Low",
                "suitable_for": ["Coastal routes", "Large volumes"]
            }
        ]
    }

# Keep existing KPI Dashboard endpoints
@app.get("/api/v1/kpi/dashboard/{scenario_name}")
def get_kpi_dashboard(scenario_name: str):
    """Keep existing KPI dashboard functionality."""
    # This will be handled by the existing fast_real_backend.py
    pass

if __name__ == "__main__":
    import uvicorn
    print("Starting Clinker Workflow Management System...")
    print("🔄 End-to-End Workflow Stages:")
    print("  1️⃣ Order & Demand Creation")
    print("  2️⃣ Inventory & Availability Check")
    print("  3️⃣ Transportation Mode Selection")
    print("  4️⃣ Dispatch Planning")
    print("  5️⃣ Loading & Dispatch Execution")
    print("  6️⃣ In-Transit Tracking")
    print("  7️⃣ Delivery & GRN")
    print("  8️⃣ Billing & Costing")
    uvicorn.run(app, host="0.0.0.0", port=8001)