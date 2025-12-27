from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd
from pyomo.environ import (
    Binary,
    ConcreteModel,
    Constraint,
    NonNegativeIntegers,
    NonNegativeReals,
    Objective,
    Param,
    Set,
    Var,
    minimize,
)


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Best-effort conversion to float with a default fallback."""

    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _ordered_unique(values: Iterable[Any]) -> List[Any]:
    """Return a list of unique values preserving first-seen order."""

    seen = set()
    ordered: List[Any] = []
    for v in values:
        if v not in seen:
            seen.add(v)
            ordered.append(v)
    return ordered


def build_clinker_model(data: Dict[str, Any]) -> ConcreteModel:
    """Build the MILP model for clinker supply chain optimization.

    Parameters
    ----------
    data:
        Dictionary of **clean, validated** pandas DataFrames and helper
        structures produced by the data layer. Expected keys:

        - ``plants``: DataFrame with at least ``plant_id``.
        - ``production_capacity_cost``: columns
            ``plant_id, period, max_capacity_tonnes, variable_cost_per_tonne``
            and optional ``holding_cost_per_tonne`` per plant/period.
        - ``transport_routes_modes``: columns
            ``origin_plant_id, destination_node_id, transport_mode,
            distance_km, cost_per_tonne, cost_per_tonne_km,
            fixed_cost_per_trip, vehicle_capacity_tonnes,
            min_batch_quantity_tonnes``.
        - ``demand_forecast``: columns
            ``customer_node_id, period, demand_tonnes``.
        - ``safety_stock_policy`` (optional): columns
            ``node_id, safety_stock_tonnes, max_inventory_tonnes``.
        - ``initial_inventory`` (optional): columns
            ``node_id, period, inventory_tonnes``.
        - ``time_periods`` (optional): ordered list of period identifiers.

    Returns
    -------
    ConcreteModel
        Fully specified Pyomo model with sets, parameters, variables,
        constraints, and objective defined.

    Notes
    -----
    - Inventory is tracked at **plants only** (location = plant_id).
    - Demand must be satisfied exactly per customer and period.
    - Safety stock and max inventory are enforced if provided.
    - SBQ is implemented with a binary activation variable per
      (origin, destination, mode, period).
    - Trips are integer and linked to shipment via per-trip capacity.
    """

    # --- Extract input dataframes -------------------------------------------------
    plants_df: pd.DataFrame = data["plants"]
    prod_df: pd.DataFrame = data["production_capacity_cost"]
    routes_df: pd.DataFrame = data["transport_routes_modes"]
    demand_df: pd.DataFrame = data["demand_forecast"]
    ss_df: pd.DataFrame = data.get("safety_stock_policy", pd.DataFrame())
    inv0_df: pd.DataFrame = data.get("initial_inventory", pd.DataFrame())

    # --- Model --------------------------------------------------------------------
    m = ConcreteModel()

    # --- Sets ---------------------------------------------------------------------
    plants = _ordered_unique(plants_df["plant_id"].tolist())
    customers = _ordered_unique(demand_df["customer_node_id"].tolist())
    modes = _ordered_unique(routes_df["transport_mode"].tolist())

    if "time_periods" in data and data["time_periods"]:
        periods = list(data["time_periods"])
    else:
        periods = _ordered_unique(demand_df["period"].tolist())

    # Route index: existing (origin, destination, mode) tuples
    routes: List[Tuple[str, str, str]] = [
        (r["origin_plant_id"], r["destination_node_id"], r["transport_mode"])
        for _, r in routes_df.iterrows()
    ]

    m.I = Set(initialize=plants, ordered=True)  # plants
    m.J = Set(initialize=customers, ordered=True)  # demand nodes
    m.M = Set(initialize=modes, ordered=True)  # transport modes
    m.T = Set(initialize=periods, ordered=True)  # time periods
    m.R = Set(initialize=routes, dimen=3, ordered=True)  # (i, j, mode)

    # Helper: previous period map computed from the ordered Python list
    prev_map: Dict[Any, Any] = {}
    for idx, p in enumerate(periods):
        prev_map[p] = None if idx == 0 else periods[idx - 1]

    m.prev_t = Param(
        m.T,
        initialize=lambda _m, t: prev_map.get(t, None),
    )

    # --- Parameters ---------------------------------------------------------------
    # Production capacity and variable/holding costs per (plant, period)
    prod_cap_dict: Dict[Tuple[str, Any], float] = {}
    prod_cost_dict: Dict[Tuple[str, Any], float] = {}
    hold_cost_dict: Dict[str, float] = {}

    for _, row in prod_df.iterrows():
        key = (row["plant_id"], row["period"])
        prod_cap_dict[key] = _safe_float(row.get("max_capacity_tonnes"), 0.0)
        prod_cost_dict[key] = _safe_float(row.get("variable_cost_per_tonne"), 0.0)
        # Holding cost can reasonably be plant-level; take average over periods
        plant_id = row["plant_id"]
        hc = row.get("holding_cost_per_tonne")
        if plant_id not in hold_cost_dict:
            hold_cost_dict[plant_id] = _safe_float(hc, 0.0)

    # Demand per (customer, period)
    demand_dict: Dict[Tuple[str, Any], float] = {}
    for _, row in demand_df.iterrows():
        key = (row["customer_node_id"], row["period"])
        demand_dict[key] = _safe_float(row.get("demand_tonnes"), 0.0)

    # Initial inventory per plant (use first period entry if multiple)
    inv0_dict: Dict[str, float] = {i: 0.0 for i in plants}
    if not inv0_df.empty:
        # Filter to plants only
        for _, row in inv0_df.iterrows():
            node = row["node_id"]
            if node in inv0_dict:
                inv0_dict[node] = _safe_float(row.get("inventory_tonnes"), 0.0)

    # Safety stock and max inventory per plant
    ss_dict: Dict[str, float] = {i: 0.0 for i in plants}
    max_inv_dict: Dict[str, float] = {i: float("inf") for i in plants}
    if not ss_df.empty:
        for _, row in ss_df.iterrows():
            node = row["node_id"]
            if node in ss_dict:
                ss_dict[node] = _safe_float(row.get("safety_stock_tonnes"), 0.0)
                max_inv_val = row.get("max_inventory_tonnes")
                if max_inv_val is not None:
                    max_inv_dict[node] = _safe_float(max_inv_val, float("inf"))

    # Transport costs and capacities per route (i, j, mode)
    trans_cost_dict: Dict[Tuple[str, str, str], float] = {}
    fixed_trip_cost_dict: Dict[Tuple[str, str, str], float] = {}
    vehicle_cap_dict: Dict[Tuple[str, str, str], float] = {}
    sbq_dict: Dict[Tuple[str, str, str], float] = {}

    for _, row in routes_df.iterrows():
        key = (row["origin_plant_id"], row["destination_node_id"], row["transport_mode"])
        distance_km = _safe_float(row.get("distance_km"), 0.0)
        cost_per_tonne = row.get("cost_per_tonne")
        cost_per_tonne_km = row.get("cost_per_tonne_km")

        if cost_per_tonne is not None:
            c = _safe_float(cost_per_tonne, 0.0)
        elif cost_per_tonne_km is not None and distance_km > 0.0:
            c = _safe_float(cost_per_tonne_km, 0.0) * distance_km
        else:
            c = 0.0

        trans_cost_dict[key] = c
        fixed_trip_cost_dict[key] = _safe_float(row.get("fixed_cost_per_trip"), 0.0)
        vehicle_cap_dict[key] = _safe_float(row.get("vehicle_capacity_tonnes"), 0.0)
        sbq_dict[key] = _safe_float(row.get("min_batch_quantity_tonnes"), 0.0)

    # Big-M for SBQ upper bound: based on vehicle capacity and total demand
    total_demand = sum(demand_dict.values()) or 1.0
    big_m = total_demand

    # Register Python dicts on the model for later cost breakdown
    m._prod_cost = prod_cost_dict
    m._trans_cost = trans_cost_dict
    m._fixed_trip_cost = fixed_trip_cost_dict
    m._hold_cost = hold_cost_dict

    # Pyomo Params ---------------------------------------------------------------
    m.cap = Param(
        m.I,
        m.T,
        initialize=lambda _m, i, t: prod_cap_dict.get((i, t), 0.0),
        within=NonNegativeReals,
    )
    m.demand = Param(
        m.J,
        m.T,
        initialize=lambda _m, j, t: demand_dict.get((j, t), 0.0),
        within=NonNegativeReals,
    )
    m.inv0 = Param(m.I, initialize=lambda _m, i: inv0_dict.get(i, 0.0), within=NonNegativeReals)
    m.ss = Param(m.I, initialize=lambda _m, i: ss_dict.get(i, 0.0), within=NonNegativeReals)
    m.max_inv = Param(m.I, initialize=lambda _m, i: max_inv_dict.get(i, float("inf")))
    m.prod_cost = Param(
        m.I,
        m.T,
        initialize=lambda _m, i, t: prod_cost_dict.get((i, t), 0.0),
    )
    m.hold_cost = Param(
        m.I,
        initialize=lambda _m, i: hold_cost_dict.get(i, 0.0),
    )
    m.trans_cost = Param(
        m.R,
        initialize=lambda _m, i, j, mode: trans_cost_dict.get((i, j, mode), 0.0),
    )
    m.fixed_trip_cost = Param(
        m.R,
        initialize=lambda _m, i, j, mode: fixed_trip_cost_dict.get((i, j, mode), 0.0),
    )
    m.vehicle_cap = Param(
        m.R,
        initialize=lambda _m, i, j, mode: vehicle_cap_dict.get((i, j, mode), 0.0),
    )
    m.sbq = Param(
        m.R,
        initialize=lambda _m, i, j, mode: sbq_dict.get((i, j, mode), 0.0),
    )

    # --- Decision variables ------------------------------------------------------
    # Production per plant & period
    m.prod = Var(m.I, m.T, domain=NonNegativeReals)
    # Shipments per route & period (continuous tonnage)
    m.ship = Var(m.R, m.T, domain=NonNegativeReals)
    # Integer number of trips per route & period
    m.trips = Var(m.R, m.T, domain=NonNegativeIntegers)
    # Binary activation variable for SBQ per route & period
    m.use_mode = Var(m.R, m.T, domain=Binary)
    # Inventory at plants per period
    m.inv = Var(m.I, m.T, domain=NonNegativeReals)

    # --- Constraints -------------------------------------------------------------

    # Production capacity limits per plant & period
    def prod_capacity_rule(_m, i, t):
        return _m.prod[i, t] <= _m.cap[i, t]

    m.prod_capacity = Constraint(m.I, m.T, rule=prod_capacity_rule)

    # Inventory balance at plants
    def inv_balance_rule(_m, i, t):
        prev_t = _m.prev_t[t]
        if prev_t is None:
            inv_prev = _m.inv0[i]
        else:
            inv_prev = _m.inv[i, prev_t]

        outbound = sum(_m.ship[i, j, mode, t] for (ii, j, mode) in _m.R if ii == i)
        return inv_prev + _m.prod[i, t] == outbound + _m.inv[i, t]

    m.inv_balance = Constraint(m.I, m.T, rule=inv_balance_rule)

    # Safety stock and max inventory at plants
    def safety_stock_rule(_m, i, t):
        return _m.inv[i, t] >= _m.ss[i]

    m.safety_stock = Constraint(m.I, m.T, rule=safety_stock_rule)

    def max_inventory_rule(_m, i, t):
        return _m.inv[i, t] <= _m.max_inv[i]

    m.max_inventory = Constraint(m.I, m.T, rule=max_inventory_rule)

    # Demand satisfaction per customer & period
    def demand_satisfaction_rule(_m, j, t):
        inbound = sum(
            _m.ship[i, j2, mode, t]
            for (i, j2, mode) in _m.R
            if j2 == j
        )
        return inbound == _m.demand[j, t]

    m.demand_satisfaction = Constraint(m.J, m.T, rule=demand_satisfaction_rule)

    # Per-trip transport capacity per route & period
    def trip_capacity_rule(_m, i, j, mode, t):
        return _m.ship[i, j, mode, t] <= _m.vehicle_cap[i, j, mode] * _m.trips[i, j, mode, t]

    m.trip_capacity = Constraint(m.R, m.T, rule=trip_capacity_rule)

    # Minimum batch quantity (SBQ) with activation binary
    def sbq_lower_rule(_m, i, j, mode, t):
        return _m.ship[i, j, mode, t] >= _m.sbq[i, j, mode] * _m.use_mode[i, j, mode, t]

    m.sbq_lower = Constraint(m.R, m.T, rule=sbq_lower_rule)

    def sbq_upper_rule(_m, i, j, mode, t):
        # Big-M upper bound to link activation to positive shipments
        return _m.ship[i, j, mode, t] <= big_m * _m.use_mode[i, j, mode, t]

    m.sbq_upper = Constraint(m.R, m.T, rule=sbq_upper_rule)

    # --- Objective: minimize total cost -----------------------------------------
    def total_cost_rule(_m):
        prod_cost_total = sum(
            _m.prod_cost[i, t] * _m.prod[i, t]
            for i in _m.I
            for t in _m.T
        )
        trans_cost_total = sum(
            _m.trans_cost[i, j, mode] * _m.ship[i, j, mode, t]
            for (i, j, mode) in _m.R
            for t in _m.T
        )
        fixed_trip_total = sum(
            _m.fixed_trip_cost[i, j, mode] * _m.trips[i, j, mode, t]
            for (i, j, mode) in _m.R
            for t in _m.T
        )
        holding_cost_total = sum(
            _m.hold_cost[i] * _m.inv[i, t]
            for i in _m.I
            for t in _m.T
        )
        return prod_cost_total + trans_cost_total + fixed_trip_total + holding_cost_total

    m.total_cost = Objective(rule=total_cost_rule, sense=minimize)

    return m
