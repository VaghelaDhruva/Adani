from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class KPIDashboard(BaseModel):
    scenario_name: str
    total_cost: float
    production_cost: float
    transport_cost: float
    holding_cost: float
    service_level: float
    stockout_risk: float
    capacity_utilization: Dict[str, float]
    inventory_vs_safety_stock: Dict[str, float]
    cost_breakdown_by_mode: Dict[str, float]
    created_at: str


class ScenarioComparison(BaseModel):
    scenarios: List[KPIDashboard]


class OptimizationResult(BaseModel):
    scenario_name: str
    status: str
    total_cost: Optional[float] = None
    runtime_seconds: Optional[float] = None
    solver: Optional[str] = None
    mip_gap: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
