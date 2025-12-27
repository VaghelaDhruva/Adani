from typing import Dict, Any, List
import pandas as pd

from app.utils.exceptions import OptimizationError


def compute_kpis(solution: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute KPIs from a solved solution and input data.
    Returns dict with total cost breakdown, service level, stockout risk, capacity utilization.
    """
    try:
        df_prod = pd.DataFrame(solution["production"])
        df_ship = pd.DataFrame(solution["shipments"])
        df_inv = pd.DataFrame(solution["inventory"])

        # Cost breakdown (placeholder; real implementation should use data dict)
        production_cost = df_prod["tonnes"].sum() * 5.0  # placeholder unit cost
        transport_cost = df_ship["tonnes"].sum() * 2.0
        holding_cost = df_inv["tonnes"].sum() * 0.5
        total_cost = production_cost + transport_cost + holding_cost

        # Service level: fraction of demand satisfied (assume all satisfied in feasible solution)
        demand_satisfied_tonnes = df_ship["tonnes"].sum()
        total_demand_tonnes = sum(d["demand_tonnes"] for d in data.get("demand_forecast", []))
        service_level = demand_satisfied_tonnes / total_demand_tonnes if total_demand_tonnes else 1.0

        # Stockout risk: placeholder (0 if solution feasible)
        stockout_risk = 0.0

        # Capacity utilization per plant
        capacity = {p["plant_id"]: p["max_capacity_tonnes"] for p in data.get("production_capacity_cost", [])}
        prod_by_plant = df_prod.groupby("plant")["tonnes"].sum().to_dict()
        capacity_utilization = {
            plant: prod_by_plant.get(plant, 0) / capacity.get(plant, 1)
            for plant in capacity
        }

        # Inventory vs safety stock
        safety_stock = {p["node_id"]: p["safety_stock_tonnes"] for p in data.get("safety_stock_policy", [])}
        inv_by_plant_period = df_inv.groupby(["plant", "period"])["tonnes"].sum().reset_index()
        inventory_vs_safety = {}
        for _, row in inv_by_plant_period.iterrows():
            plant = row["plant"]
            period = row["period"]
            inv = row["tonnes"]
            ss = safety_stock.get(plant, 0)
            inventory_vs_safety[f"{plant}_{period}"] = {"inventory": inv, "safety_stock": ss}

        return {
            "total_cost": total_cost,
            "production_cost": production_cost,
            "transport_cost": transport_cost,
            "holding_cost": holding_cost,
            "service_level": service_level,
            "stockout_risk": stockout_risk,
            "capacity_utilization": capacity_utilization,
            "inventory_vs_safety_stock": inventory_vs_safety,
        }
    except Exception as e:
        raise OptimizationError(f"KPI calculation failed: {e}")
