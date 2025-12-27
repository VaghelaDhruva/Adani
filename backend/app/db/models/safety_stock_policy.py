from sqlalchemy import Column, Integer, String, Float, DateTime

from app.db.base import Base


class SafetyStockPolicy(Base):
    __tablename__ = "safety_stock_policy"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String, nullable=False)  # plant or customer
    policy_type = Column(String, nullable=False)  # days_of_cover, percentage_of_demand, absolute
    policy_value = Column(Float, nullable=False)  # e.g., 7 days, 0.15 (15%), 500 tonnes
    safety_stock_tonnes = Column(Float)  # computed after demand is known
    max_inventory_tonnes = Column(Float)  # optional capacity limit
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now()")
