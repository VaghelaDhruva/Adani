"""
Staging Tables for Data Safety Pipeline

These tables receive raw CSV/ERP data before validation.
NO production code should read from staging tables.
Only the validation pipeline moves data from staging -> clean tables.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, text
from app.db.base import Base


class StagingPlantMaster(Base):
    """Staging table for plant master data"""
    __tablename__ = "stg_plant_master"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(String)  # No constraints in staging
    plant_name = Column(String)
    plant_type = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    region = Column(String)
    country = Column(String)
    
    # Staging metadata
    batch_id = Column(String, nullable=False)  # Track upload batches
    source_file = Column(String)
    source_row = Column(Integer)  # Original row number in CSV
    validation_status = Column(String, default="pending")  # pending, valid, invalid
    validation_errors = Column(Text)  # JSON array of errors
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class StagingDemandForecast(Base):
    """Staging table for demand forecast data"""
    __tablename__ = "stg_demand_forecast"

    id = Column(Integer, primary_key=True, index=True)
    customer_node_id = Column(String)
    period = Column(String)
    demand_tonnes = Column(Float)
    demand_low_tonnes = Column(Float)
    demand_high_tonnes = Column(Float)
    confidence_level = Column(Float)
    source = Column(String)
    
    # Staging metadata
    batch_id = Column(String, nullable=False)
    source_file = Column(String)
    source_row = Column(Integer)
    validation_status = Column(String, default="pending")
    validation_errors = Column(Text)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class StagingTransportRoutes(Base):
    """Staging table for transport routes data"""
    __tablename__ = "stg_transport_routes"

    id = Column(Integer, primary_key=True, index=True)
    origin_plant_id = Column(String)
    destination_node_id = Column(String)
    transport_mode = Column(String)
    distance_km = Column(Float)
    cost_per_tonne = Column(Float)
    cost_per_tonne_km = Column(Float)
    fixed_cost_per_trip = Column(Float)
    vehicle_capacity_tonnes = Column(Float)
    min_batch_quantity_tonnes = Column(Float)
    lead_time_days = Column(Float)
    is_active = Column(String)
    
    # Staging metadata
    batch_id = Column(String, nullable=False)
    source_file = Column(String)
    source_row = Column(Integer)
    validation_status = Column(String, default="pending")
    validation_errors = Column(Text)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class StagingProductionCosts(Base):
    """Staging table for production costs data"""
    __tablename__ = "stg_production_costs"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(String)
    period = Column(String)
    max_capacity_tonnes = Column(Float)
    variable_cost_per_tonne = Column(Float)
    fixed_cost_per_period = Column(Float)
    min_run_level = Column(Float)
    holding_cost_per_tonne = Column(Float)
    
    # Staging metadata
    batch_id = Column(String, nullable=False)
    source_file = Column(String)
    source_row = Column(Integer)
    validation_status = Column(String, default="pending")
    validation_errors = Column(Text)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class StagingInitialInventory(Base):
    """Staging table for initial inventory data"""
    __tablename__ = "stg_initial_inventory"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String)
    period = Column(String)
    inventory_tonnes = Column(Float)
    
    # Staging metadata
    batch_id = Column(String, nullable=False)
    source_file = Column(String)
    source_row = Column(Integer)
    validation_status = Column(String, default="pending")
    validation_errors = Column(Text)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class StagingSafetyStock(Base):
    """Staging table for safety stock policy data"""
    __tablename__ = "stg_safety_stock"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String)
    policy_type = Column(String)
    policy_value = Column(Float)
    effective_from = Column(String)
    effective_to = Column(String)
    
    # Staging metadata
    batch_id = Column(String, nullable=False)
    source_file = Column(String)
    source_row = Column(Integer)
    validation_status = Column(String, default="pending")
    validation_errors = Column(Text)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class ValidationBatch(Base):
    """Track validation batches and their status"""
    __tablename__ = "validation_batch"

    batch_id = Column(String, primary_key=True)
    source_file = Column(String, nullable=False)
    table_name = Column(String, nullable=False)
    total_rows = Column(Integer, nullable=False)
    valid_rows = Column(Integer, default=0)
    invalid_rows = Column(Integer, default=0)
    status = Column(String, default="pending")  # pending, validated, promoted, failed
    validation_errors = Column(Text)  # Summary of validation errors
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    validated_at = Column(DateTime)
    promoted_at = Column(DateTime)  # When moved to production tables