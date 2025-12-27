from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey

from app.db.base import Base


class ProductionCapacityCost(Base):
    __tablename__ = "production_capacity_cost"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(String, ForeignKey("plant_master.plant_id"), nullable=False)
    period = Column(String, nullable=False)  # e.g., 2025-W01, 2025-01
    max_capacity_tonnes = Column(Float, nullable=False)
    variable_cost_per_tonne = Column(Float, nullable=False)
    fixed_cost_per_period = Column(Float, default=0.0)
    min_run_level = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now()")
