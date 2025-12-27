import math
from typing import Any, Dict, List, Tuple

import pandas as pd

from app.services.optimization.model_builder import build_clinker_model
from app.services.optimization.solvers import solve_model
from app.services.optimization.result_parser import extract_solution


TOL = 1e-6


def _build_basic_data(no_sbq: bool = True) -> Dict[str, Any]:
    """Build a tiny synthetic dataset for optimization tests.

    Scenario:
    - 2 plants (P1, P2)
    - 2 customers (C1, C2)
    - 2 periods (t1, t2)
    - Production capacity > total demand
    - Simple linear costs
    - Vehicle capacity large enough
    - SBQ = 0 if no_sbq is True, else positive with fixed trip cost
    """

    plants = pd.DataFrame(
        [
            {"plant_id": "P1"},
            {"plant_id": "P2"},
        ]
    )

    periods = ["t1", "t2"]

    # Production capacity and cost per plant-period
    prod_records: List[Dict[str, Any]] = []
    for plant_id in ["P1", "P2"]:
        for period in periods:
            prod_records.append(
                {
                    "plant_id": plant_id,
                    "period": period,
                    "max_capacity_tonnes": 200.0,  # capacity > total demand
                    "variable_cost_per_tonne": 10.0 if plant_id == "P1" else 12.0,
                    "holding_cost_per_tonne": 1.0,
                }
            )
    production_capacity_cost = pd.DataFrame(prod_records)

    # Two customers with symmetric demand in both periods
    demand_records: List[Dict[str, Any]] = []
    for customer in ["C1", "C2"]:
        for period in periods:
            demand_records.append(
                {
                    "customer_node_id": customer,
                    "period": period,
                    "demand_tonnes": 50.0,  # total demand per period = 100
                }
            )
    demand_forecast = pd.DataFrame(demand_records)

    # Transport network: each plant can serve each customer via road
    routes: List[Dict[str, Any]] = []
    for origin in ["P1", "P2"]:
        for dest in ["C1", "C2"]:
            routes.append(
                {
                    "origin_plant_id": origin,
                    "destination_node_id": dest,
                    "transport_mode": "road",
                    "distance_km": 100.0,
                    "cost_per_tonne": 5.0 if origin == "P1" else 6.0,
                    "cost_per_tonne_km": None,
                    "fixed_cost_per_trip": 0.0 if no_sbq else 100.0,
                    "vehicle_capacity_tonnes": 1_000.0,
                    "min_batch_quantity_tonnes": 0.0 if no_sbq else 20.0,
                }
            )
    transport_routes_modes = pd.DataFrame(routes)

    # Safety stock: small buffer at plants
    safety_stock_policy = pd.DataFrame(
        [
            {
                "node_id": "P1",
                "policy_type": "absolute",
                "policy_value": 0.0,
                "safety_stock_tonnes": 10.0,
                "max_inventory_tonnes": 500.0,
            },
            {
                "node_id": "P2",
                "policy_type": "absolute",
                "policy_value": 0.0,
                "safety_stock_tonnes": 5.0,
                "max_inventory_tonnes": 500.0,
            },
        ]
    )

    # Initial inventory at plants (only first period matters)
    initial_inventory = pd.DataFrame(
        [
            {"node_id": "P1", "period": "t1", "inventory_tonnes": 0.0},
            {"node_id": "P2", "period": "t1", "inventory_tonnes": 0.0},
        ]
    )

    data: Dict[str, Any] = {
        "plants": plants,
        "production_capacity_cost": production_capacity_cost,
        "transport_routes_modes": transport_routes_modes,
        "demand_forecast": demand_forecast,
        "safety_stock_policy": safety_stock_policy,
        "initial_inventory": initial_inventory,
        "time_periods": periods,
    }
    return data


def _run_model(data: Dict[str, Any], solver_name: str = "highs") -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Build model, solve it with the given solver, and return (solver_meta, solution).

    Defaults to HiGHS, which is available as a Python wheel and does not
    require a separate CBC executable to be installed on the system.
    """

    model = build_clinker_model(data)
    solver_meta = solve_model(model, solver_name=solver_name)
    solution = extract_solution(model)
    return solver_meta, solution


def test_basic_optimization_sanity():
    """End-to-end sanity test without SBQ.

    Validates:
    - All customer demands are fully satisfied per period.
    - No negative shipments or inventory.
    - Inventory balances correctly at each plant and period.
    - Objective equals the sum of the cost breakdown components.
    - Solver termination condition indicates an optimal solution.
    """

    data = _build_basic_data(no_sbq=True)
    solver_meta, solution = _run_model(data)

    # 1) Demand satisfaction per customer and period
    demand_df = data["demand_forecast"]
    demand_map: Dict[Tuple[str, str], float] = {
        (row["customer_node_id"], row["period"]): float(row["demand_tonnes"])
        for _, row in demand_df.iterrows()
    }

    shipped_by_cust_period: Dict[Tuple[str, str], float] = {}
    for s in solution["shipments"]:
        key = (s["destination"], s["period"])
        shipped_by_cust_period[key] = shipped_by_cust_period.get(key, 0.0) + s["tonnes"]

    for key, demand_val in demand_map.items():
        shipped = shipped_by_cust_period.get(key, 0.0)
        assert math.isclose(shipped, demand_val, rel_tol=1e-6, abs_tol=1e-6), (
            f"Demand not satisfied for {key}: shipped={shipped}, demand={demand_val}"
        )

    # 2) No negative shipments or inventory
    for s in solution["shipments"]:
        assert s["tonnes"] >= -TOL
    for inv in solution["inventory"]:
        assert inv["tonnes"] >= -TOL

    # 3) Inventory balance at each plant and period
    plants = ["P1", "P2"]
    periods = data["time_periods"]

    inv0_map: Dict[str, float] = {p: 0.0 for p in plants}
    for _, row in data["initial_inventory"].iterrows():
        if row["node_id"] in inv0_map:
            inv0_map[row["node_id"]] = float(row["inventory_tonnes"])

    inv_by_plant_period: Dict[Tuple[str, str], float] = {
        (rec["plant"], rec["period"]): rec["tonnes"] for rec in solution["inventory"]
    }

    shipped_by_origin_period: Dict[Tuple[str, str], float] = {}
    for s in solution["shipments"]:
        key = (s["origin"], s["period"])
        shipped_by_origin_period[key] = shipped_by_origin_period.get(key, 0.0) + s["tonnes"]

    prod_df = data["production_capacity_cost"]
    prod_by_plant_period: Dict[Tuple[str, str], float] = {}
    # Production decision is in solution["production"]
    for rec in solution["production"]:
        prod_by_plant_period[(rec["plant"], rec["period"])] = rec["tonnes"]

    for plant in plants:
        for idx, period in enumerate(periods):
            if idx == 0:
                inv_prev = inv0_map[plant]
            else:
                inv_prev = inv_by_plant_period[(plant, periods[idx - 1])]
            prod = prod_by_plant_period.get((plant, period), 0.0)
            outbound = shipped_by_origin_period.get((plant, period), 0.0)
            inv = inv_by_plant_period.get((plant, period), 0.0)

            lhs = inv_prev + prod
            rhs = outbound + inv
            assert math.isclose(lhs, rhs, rel_tol=1e-6, abs_tol=1e-6), (
                f"Inventory balance violated for plant={plant}, period={period}: "
                f"prev+prod={lhs}, outbound+inv={rhs}"
            )

    # 4) Objective matches cost breakdown
    cost = solution["cost_breakdown"]
    breakdown_sum = (
        cost["production_cost"]
        + cost["transport_cost"]
        + cost["fixed_trip_cost"]
        + cost["holding_cost"]
    )
    assert math.isclose(
        solution["objective"], breakdown_sum, rel_tol=1e-6, abs_tol=1e-6
    )
    assert math.isclose(
        cost["total_cost"], breakdown_sum, rel_tol=1e-6, abs_tol=1e-6
    )

    # 5) Solver termination indicates optimal solution
    assert "optimal" in solver_meta["termination"].lower()


def test_optimization_with_sbq_and_fixed_trips():
    """End-to-end test with SBQ and fixed trip costs.

    Validates:
    - Trips decision variable is integer-valued.
    - When a route is active (shipment > 0), shipment obeys SBQ lower bound.
    """

    data = _build_basic_data(no_sbq=False)
    solver_meta, solution = _run_model(data)

    # Trips are integer (within tolerance) and non-negative
    for rec in solution["trips"]:
        trips_val = rec["trips"]
        assert trips_val >= 0
        assert isinstance(trips_val, int)

    # Shipments obey SBQ when active
    # Build a map for SBQ by (origin, dest, mode)
    routes_df = data["transport_routes_modes"]
    sbq_map: Dict[Tuple[str, str, str], float] = {}
    for _, row in routes_df.iterrows():
        key = (row["origin_plant_id"], row["destination_node_id"], row["transport_mode"])
        sbq_map[key] = float(row.get("min_batch_quantity_tonnes", 0.0))

    for s in solution["shipments"]:
        key = (s["origin"], s["destination"], s["mode"])
        sbq = sbq_map.get(key, 0.0)
        if sbq > 0.0 and s["tonnes"] > TOL:
            assert s["tonnes"] + TOL >= sbq, (
                f"SBQ not respected on {key}: shipped={s['tonnes']}, sbq={sbq}"
            )

    # Still expect optimal termination
    assert "optimal" in solver_meta["termination"].lower()
