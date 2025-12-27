from pydantic import BaseModel
from typing import Optional


class ScenarioMetadataBase(BaseModel):
    scenario_name: str
    description: Optional[str] = None
    demand_multiplier: Optional[float] = 1.0
    transport_cost_multiplier: Optional[float] = 1.0
    production_cost_multiplier: Optional[float] = 1.0
    solver: Optional[str] = "cbc"
    time_limit_seconds: Optional[int] = 600
    mip_gap: Optional[float] = 0.01
    status: Optional[str] = "draft"
    created_by: Optional[str] = None


class ScenarioMetadataCreate(ScenarioMetadataBase):
    pass


class ScenarioMetadataUpdate(BaseModel):
    description: Optional[str] = None
    demand_multiplier: Optional[float] = None
    transport_cost_multiplier: Optional[float] = None
    production_cost_multiplier: Optional[float] = None
    solver: Optional[str] = None
    time_limit_seconds: Optional[int] = None
    mip_gap: Optional[float] = None
    status: Optional[str] = None


class ScenarioMetadata(ScenarioMetadataBase):
    id: int

    class Config:
        from_attributes = True
