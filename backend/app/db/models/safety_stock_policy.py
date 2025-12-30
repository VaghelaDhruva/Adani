
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, text


from app.db.base import Base


class SafetyStockPolicy(Base):
    __tablename__ = "safety_stock_policy"

    id = Column(Integer, primary_key=True, index=True)

    node_id = Column(String, nullable=False)  # plant or customer
    policy_type = Column(String, nullable=False)  # days_of_cover, percentage_of_demand, absolute
    policy_value = Column(Float, nullable=False)  # e.g., 7 days, 0.15 (15%), 500 tonnes
    safety_stock_tonnes = Column(Float)  # computed after demand is known
    max_inventory_tonnes = Column(Float)  # optional capacity limit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    location_id = Column(String, nullable=False)  # plant_id or customer_node_id
    product_type = Column(String, default="clinker")
    safety_stock_tonnes = Column(Float, nullable=False)
    safety_stock_days = Column(Float)  # alternative specification in days of demand
    penalty_cost_per_tonne = Column(Float, default=1000.0)  # cost of stockout
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
