from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func

from app.db.base import Base


class KPISnapshot(Base):
    __tablename__ = "kpi_snapshot"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(255), ForeignKey("optimization_run.run_id"), nullable=False, index=True)
    scenario_name = Column(String(255), nullable=False, index=True)
    snapshot_timestamp = Column(DateTime, server_default=func.now(), index=True)
    
    # Financial KPIs
    total_cost = Column(Float, nullable=False)
    cost_per_tonne = Column(Float)
    cost_breakdown = Column(JSON)  # detailed cost components
    
    # Operational KPIs
    total_production = Column(Float)
    total_shipments = Column(Float)
    average_utilization = Column(Float)
    
    # Service KPIs
    service_level = Column(Float)
    demand_fulfillment_rate = Column(Float)
    on_time_delivery_rate = Column(Float)
    stockout_frequency = Column(Float)
    
    # Efficiency KPIs
    transport_efficiency = Column(Float)
    inventory_turns = Column(Float)
    capacity_utilization = Column(Float)
    
    # Quality KPIs
    sbq_compliance_rate = Column(Float)
    safety_stock_compliance = Column(Float)
    
    # Detailed metrics
    kpi_details = Column(JSON)  # full KPI breakdown for dashboard
    
    created_at = Column(DateTime, server_default=func.now())