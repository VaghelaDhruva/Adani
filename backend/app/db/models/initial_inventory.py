<<<<<<< HEAD
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
=======
from sqlalchemy import Column, Integer, String, Float, DateTime, text
>>>>>>> d4196135 (Fixed Bug)

from app.db.base import Base


class InitialInventory(Base):
    __tablename__ = "initial_inventory"

    id = Column(Integer, primary_key=True, index=True)
<<<<<<< HEAD
    node_id = Column(String, nullable=False)
    period = Column(String, nullable=False)
    inventory_tonnes = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
=======
    location_id = Column(String, nullable=False)  # plant_id or customer_node_id
    product_type = Column(String, default="clinker")
    initial_stock_tonnes = Column(Float, nullable=False)
    unit_cost = Column(Float, default=0.0)  # cost per tonne for valuation
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
>>>>>>> d4196135 (Fixed Bug)
