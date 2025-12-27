from sqlalchemy import Column, Integer, String, Float, DateTime

from app.db.base import Base


class DemandForecast(Base):
    __tablename__ = "demand_forecast"

    id = Column(Integer, primary_key=True, index=True)
    customer_node_id = Column(String, nullable=False)
    period = Column(String, nullable=False)  # e.g., 2025-W01, 2025-01
    demand_tonnes = Column(Float, nullable=False)
    demand_low_tonnes = Column(Float)  # optional lower bound
    demand_high_tonnes = Column(Float)  # optional upper bound
    confidence_level = Column(Float)  # e.g., 0.95
    source = Column(String)  # manual, api, forecast_model
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now()")
