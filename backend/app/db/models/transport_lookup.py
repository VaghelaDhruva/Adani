from sqlalchemy import Column, Integer, String, Float, DateTime, text, UniqueConstraint
from sqlalchemy.orm import Session

from app.db.base import Base


class TransportLookup(Base):
    __tablename__ = "transport_lookup"

    id = Column(Integer, primary_key=True, index=True)
    origin_plant_id = Column(String, nullable=False, index=True)
    destination_node_id = Column(String, nullable=False, index=True)
    transport_mode = Column(String, nullable=False, index=True)
    distance_km = Column(Float, nullable=False)
    duration_minutes = Column(Float, nullable=False)
    source = Column(String, nullable=False)  # "OSRM" or "ORS"
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        UniqueConstraint(
            "origin_plant_id", "destination_node_id", "transport_mode", name="uq_transport_lookup_route"
        ),
        {"sqlite_autoincrement": True},
    )
