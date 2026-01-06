"""
Precomputed KPI Tables for Fast Dashboard Loading

Stores pre-aggregated KPIs to avoid expensive calculations on every dashboard load.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Index
from sqlalchemy.sql import func

from app.db.base import Base


class KPIPrecomputed(Base):
    """Precomputed KPI snapshot for fast dashboard loading."""
    
    __tablename__ = "kpi_precomputed"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Reference to optimization run
    optimization_run_id = Column(Integer, nullable=False, index=True)
    scenario_name = Column(String(255), nullable=False, index=True)
    
    # Period
    period = Column(String(50), nullable=True, index=True)
    
    # Cost KPIs (all in RAW RUPEES)
    total_cost = Column(Float, nullable=False)
    production_cost = Column(Float, nullable=False)
    transport_cost = Column(Float, nullable=False)
    fixed_trip_cost = Column(Float, nullable=False)
    holding_cost = Column(Float, nullable=False)
    penalty_cost = Column(Float, nullable=False)
    
    # Production KPIs
    total_production_tonnes = Column(Float, nullable=False)
    production_utilization = Column(Float, nullable=False)  # 0-1
    
    # Transport KPIs
    total_shipment_tonnes = Column(Float, nullable=False)
    total_trips = Column(Integer, nullable=False)
    transport_utilization = Column(Float, nullable=False)  # 0-1
    sbq_compliance_rate = Column(Float, nullable=False)  # 0-1
    
    # Inventory KPIs
    average_inventory_tonnes = Column(Float, nullable=False)
    inventory_turns = Column(Float, nullable=False)
    
    # Service KPIs
    total_demand_tonnes = Column(Float, nullable=False)
    total_unmet_demand_tonnes = Column(Float, nullable=False)
    demand_fulfillment_rate = Column(Float, nullable=False)  # 0-1
    service_level = Column(Float, nullable=False)  # 0-1
    stockout_events = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    computed_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Indexes for fast filtering
    __table_args__ = (
        Index('idx_scenario_period', 'scenario_name', 'period'),
        Index('idx_run_scenario', 'optimization_run_id', 'scenario_name'),
    )


class KPIAggregated(Base):
    """Aggregated KPIs across all scenarios for comparison."""
    
    __tablename__ = "kpi_aggregated"
    
    id = Column(Integer, primary_key=True, index=True)
    
    scenario_name = Column(String(255), nullable=False, unique=True, index=True)
    
    # Aggregated cost (RAW RUPEES)
    total_cost = Column(Float, nullable=False)
    cost_breakdown = Column(JSON, nullable=True)  # Detailed breakdown
    
    # Summary metrics
    total_production = Column(Float, nullable=False)
    total_shipment = Column(Float, nullable=False)
    total_trips = Column(Integer, nullable=False)
    average_service_level = Column(Float, nullable=False)
    
    # Timestamps
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now(), index=True)
    created_at = Column(DateTime, server_default=func.now())

