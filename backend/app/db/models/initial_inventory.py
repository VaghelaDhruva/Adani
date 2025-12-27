from sqlalchemy import Column, Integer, String, Float, DateTime

from app.db.base import Base


class InitialInventory(Base):
    __tablename__ = "initial_inventory"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String, nullable=False)
    period = Column(String, nullable=False)
    inventory_tonnes = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now()")
