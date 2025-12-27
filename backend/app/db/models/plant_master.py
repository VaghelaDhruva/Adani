from sqlalchemy import Column, Integer, String, Float, DateTime

from app.db.base import Base


class PlantMaster(Base):
    __tablename__ = "plant_master"

    plant_id = Column(String, primary_key=True, index=True)
    plant_name = Column(String, nullable=False)
    plant_type = Column(String, nullable=False)  # e.g., clinker, grinding, terminal
    latitude = Column(Float)
    longitude = Column(Float)
    region = Column(String)
    country = Column(String)
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now()")
