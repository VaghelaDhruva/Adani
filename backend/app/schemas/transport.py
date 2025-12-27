from pydantic import BaseModel
from typing import Optional


class TransportRouteBase(BaseModel):
    origin_plant_id: str
    destination_node_id: str
    transport_mode: str
    distance_km: Optional[float] = None
    cost_per_tonne: Optional[float] = None
    cost_per_tonne_km: Optional[float] = None
    fixed_cost_per_trip: Optional[float] = 0.0
    vehicle_capacity_tonnes: float
    min_batch_quantity_tonnes: Optional[float] = 0.0
    lead_time_days: Optional[float] = None
    is_active: Optional[str] = "Y"


class TransportRouteCreate(TransportRouteBase):
    pass


class TransportRouteUpdate(BaseModel):
    distance_km: Optional[float] = None
    cost_per_tonne: Optional[float] = None
    cost_per_tonne_km: Optional[float] = None
    fixed_cost_per_trip: Optional[float] = None
    vehicle_capacity_tonnes: Optional[float] = None
    min_batch_quantity_tonnes: Optional[float] = None
    lead_time_days: Optional[float] = None
    is_active: Optional[str] = None


class TransportRoute(TransportRouteBase):
    id: int

    class Config:
        from_attributes = True
