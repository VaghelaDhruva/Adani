from pydantic import BaseModel
from typing import Optional


class InitialInventoryBase(BaseModel):
    node_id: str
    period: str
    inventory_tonnes: float


class InitialInventoryCreate(InitialInventoryBase):
    pass


class InitialInventoryUpdate(BaseModel):
    inventory_tonnes: Optional[float] = None


class InitialInventory(InitialInventoryBase):
    id: int

    class Config:
        from_attributes = True


class SafetyStockPolicyBase(BaseModel):
    node_id: str
    policy_type: str
    policy_value: float
    safety_stock_tonnes: Optional[float] = None
    max_inventory_tonnes: Optional[float] = None


class SafetyStockPolicyCreate(SafetyStockPolicyBase):
    pass


class SafetyStockPolicyUpdate(BaseModel):
    policy_type: Optional[str] = None
    policy_value: Optional[float] = None
    safety_stock_tonnes: Optional[float] = None
    max_inventory_tonnes: Optional[float] = None


class SafetyStockPolicy(SafetyStockPolicyBase):
    id: int

    class Config:
        from_attributes = True