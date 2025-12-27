from pydantic import BaseModel, Field
from typing import Optional


class DemandForecastBase(BaseModel):
    customer_node_id: str
    period: str
    demand_tonnes: float
    demand_low_tonnes: Optional[float] = None
    demand_high_tonnes: Optional[float] = None
    confidence_level: Optional[float] = None
    source: Optional[str] = None


class DemandForecastCreate(DemandForecastBase):
    pass


class DemandForecastUpdate(BaseModel):
    demand_tonnes: Optional[float] = None
    demand_low_tonnes: Optional[float] = None
    demand_high_tonnes: Optional[float] = None
    confidence_level: Optional[float] = None
    source: Optional[str] = None


class DemandForecast(DemandForecastBase):
    id: int

    class Config:
        from_attributes = True
