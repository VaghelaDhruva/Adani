from typing import Dict, Tuple, Any

Number = float
LocationPeriod = Tuple[Any, Any]


def compute_kpis(
    *,
    costs: Dict[str, Number],
    demand: Dict[LocationPeriod, Number],
    fulfilled: Dict[LocationPeriod, Number],
    plant_production: Dict[Any, Number],
    plant_capacity: Dict[Any, Number],
) -> Dict[str, Any]:
    """Compute per-scenario KPIs from aggregated optimization results.

    All inputs are simple mappings; missing keys are treated as zero.
    This function is pure: no I/O, no globals, no DB/API access.
    """

    # --- Cost KPIs ---
    production_cost = float(costs.get("production_cost", 0.0) or 0.0)
    transport_cost = float(costs.get("transport_cost", 0.0) or 0.0)
    fixed_trip_cost = float(costs.get("fixed_trip_cost", 0.0) or 0.0)
    holding_cost = float(costs.get("holding_cost", 0.0) or 0.0)

    total_cost = production_cost + transport_cost + fixed_trip_cost + holding_cost

    # --- Service level ---
    total_demand = float(sum(v or 0.0 for v in demand.values()))
    total_fulfilled = 0.0
    for key, d in demand.items():
        d_val = float(d or 0.0)
        f_val = float(fulfilled.get(key, 0.0) or 0.0)
        total_fulfilled += min(f_val, d_val)  # can't fulfill more than demand for service metric

    if total_demand == 0.0:
        service_level = 1.0
    else:
        service_level = total_fulfilled / total_demand

    # --- Stockout risk ---
    stockout_periods = 0
    periods_with_demand = 0
    for key, d in demand.items():
        d_val = float(d or 0.0)
        if d_val <= 0.0:
            continue
        periods_with_demand += 1
        f_val = float(fulfilled.get(key, 0.0) or 0.0)
        if f_val < d_val:
            stockout_periods += 1

    if periods_with_demand == 0:
        stockout_risk = 0.0
    else:
        stockout_risk = stockout_periods / periods_with_demand

    # --- Capacity utilization per plant ---
    utilization: Dict[Any, float] = {}
    plants = set(plant_production.keys()) | set(plant_capacity.keys())
    for plant in plants:
        prod = float(plant_production.get(plant, 0.0) or 0.0)
        cap = float(plant_capacity.get(plant, 0.0) or 0.0)
        if cap <= 0.0:
            util = 0.0
        else:
            util = prod / cap
        utilization[plant] = util

    return {
        "total_cost": total_cost,
        "production_cost": production_cost,
        "transport_cost": transport_cost,
        "fixed_trip_cost": fixed_trip_cost,
        "holding_cost": holding_cost,
        "service_level": service_level,
        "stockout_risk": stockout_risk,
        "capacity_utilization": utilization,
    }
