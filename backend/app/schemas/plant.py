from pydantic import BaseModel, Field
from typing import Optional


class PlantMasterBase(BaseModel):
    plant_id: str
    plant_name: str
    plant_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    region: Optional[str] = None
    country: Optional[str] = None


class PlantMasterCreate(PlantMasterBase):
    pass


class PlantMasterUpdate(BaseModel):
    plant_name: Optional[str] = None
    plant_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    region: Optional[str] = None
    country: Optional[str] = None


class PlantMaster(PlantMasterBase):
    class Config:
        from_attributes = True
