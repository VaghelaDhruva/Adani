from sqlalchemy import Column, Integer, String, Float, DateTime, Text

from app.db.base import Base


class ScenarioMetadata(Base):
    __tablename__ = "scenario_metadata"

    id = Column(Integer, primary_key=True, index=True)
    scenario_name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    demand_multiplier = Column(Float, default=1.0)
    transport_cost_multiplier = Column(Float, default=1.0)
    production_cost_multiplier = Column(Float, default=1.0)
    solver = Column(String, default="cbc")
    time_limit_seconds = Column(Integer, default=600)
    mip_gap = Column(Float, default=0.01)
    status = Column(String, default="draft")  # draft, running, completed, failed
    created_by = Column(String)
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now()")
