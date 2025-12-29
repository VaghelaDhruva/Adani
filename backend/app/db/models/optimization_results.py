from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class OptimizationResults(Base):
    __tablename__ = "optimization_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(255), ForeignKey("optimization_run.run_id"), nullable=False, index=True)
    
    # Cost breakdown
    total_cost = Column(Float, nullable=False)
    production_cost = Column(Float, nullable=False)
    transport_cost = Column(Float, nullable=False)
    inventory_cost = Column(Float, nullable=False)
    penalty_cost = Column(Float, default=0.0)
    
    # Production results
    production_plan = Column(JSON)  # {plant_id: {period: production_amount}}
    production_utilization = Column(JSON)  # {plant_id: utilization_percentage}
    
    # Transport results
    shipment_plan = Column(JSON)  # {(origin, destination, mode, period): quantity}
    transport_utilization = Column(JSON)  # {mode: utilization_stats}
    
    # Inventory results
    inventory_profile = Column(JSON)  # {location: {period: inventory_level}}
    safety_stock_violations = Column(JSON)  # {location: {period: violation_amount}}
    
    # Service performance
    demand_fulfillment = Column(JSON)  # {location: {period: {demand, fulfilled, backorder}}}
    service_level = Column(Float)  # overall service level percentage
    stockout_events = Column(Integer, default=0)
    
    # Capacity utilization
    capacity_utilization = Column(JSON)  # {plant_id: {period: utilization}}
    capacity_violations = Column(JSON)  # {plant_id: {period: violation_amount}}
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship
    optimization_run = relationship("OptimizationRun", backref="results")