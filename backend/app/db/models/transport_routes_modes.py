from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, text

from app.db.base import Base


class TransportRoutesModes(Base):
    __tablename__ = "transport_routes_modes"

    id = Column(Integer, primary_key=True, index=True)
    origin_plant_id = Column(String, ForeignKey("plant_master.plant_id", ondelete="CASCADE"), nullable=False)
    destination_node_id = Column(String, nullable=False)  # could be plant or customer
    transport_mode = Column(String, nullable=False)  # road, rail, sea, barge
    distance_km = Column(Float)
    cost_per_tonne = Column(Float)
    cost_per_tonne_km = Column(Float)
    fixed_cost_per_trip = Column(Float, default=0.0)
    vehicle_capacity_tonnes = Column(Float, nullable=False)
    min_batch_quantity_tonnes = Column(Float, default=0.0)
    lead_time_days = Column(Float)
    is_active = Column(String, default="Y")
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
