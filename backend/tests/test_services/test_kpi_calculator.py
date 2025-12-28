import math

from app.services.kpi_calculator import compute_kpis


def test_kpi_happy_path():
    costs = {
        "production_cost": 100.0,
        "transport_cost": 50.0,
        "fixed_trip_cost": 25.0,
        "holding_cost": 10.0,
    }
    # (location, period) -> qty
    demand = {
        ("C1", "2025-01"): 100.0,
        ("C1", "2025-02"): 50.0,
    }
    fulfilled = {
        ("C1", "2025-01"): 90.0,   # partial fulfillment
        ("C1", "2025-02"): 50.0,   # fully met
    }
    plant_production = {"P1": 120.0}
    plant_capacity = {"P1": 200.0}

    kpis = compute_kpis(
        costs=costs,
        demand=demand,
        fulfilled=fulfilled,
        plant_production=plant_production,
        plant_capacity=plant_capacity,
    )

    assert kpis["total_cost"] == 100.0 + 50.0 + 25.0 + 10.0
    assert kpis["production_cost"] == 100.0
    assert kpis["transport_cost"] == 50.0
    assert kpis["fixed_trip_cost"] == 25.0
    assert kpis["holding_cost"] == 10.0

    # total_demand = 150, total_fulfilled = 140 (90 + 50)
    assert math.isclose(kpis["service_level"], 140.0 / 150.0, rel_tol=1e-9)

    # periods_with_demand = 2; stockout_periods = 1 (first period partial)
    assert math.isclose(kpis["stockout_risk"], 1.0 / 2.0, rel_tol=1e-9)

    util = kpis["capacity_utilization"]
    assert set(util.keys()) == {"P1"}
    assert math.isclose(util["P1"], 120.0 / 200.0, rel_tol=1e-9)


def test_kpi_zero_demand():
    costs = {"production_cost": 0.0, "transport_cost": 0.0}
    demand = {}
    fulfilled = {}
    plant_production = {}
    plant_capacity = {}

    kpis = compute_kpis(
        costs=costs,
        demand=demand,
        fulfilled=fulfilled,
        plant_production=plant_production,
        plant_capacity=plant_capacity,
    )

    # By spec
    assert kpis["service_level"] == 1.0
    assert kpis["stockout_risk"] == 0.0


def test_kpi_partial_stockout_fraction():
    # 3 periods with demand, 2 stockouts
    demand = {
        ("C1", "t1"): 10.0,
        ("C1", "t2"): 20.0,
        ("C1", "t3"): 30.0,
    }
    fulfilled = {
        ("C1", "t1"): 10.0,   # full
        ("C1", "t2"): 0.0,    # none
        ("C1", "t3"): 10.0,   # partial
    }

    kpis = compute_kpis(
        costs={},
        demand=demand,
        fulfilled=fulfilled,
        plant_production={},
        plant_capacity={},
    )

    # periods_with_demand = 3; stockout_periods = 2 (t2 and t3)
    assert math.isclose(kpis["stockout_risk"], 2.0 / 3.0, rel_tol=1e-9)


def test_kpi_zero_capacity_utilization():
    demand = {("C1", "t1"): 10.0}
    fulfilled = {("C1", "t1"): 10.0}
    plant_production = {"P1": 50.0, "P2": 0.0}
    plant_capacity = {"P1": 0.0, "P2": 0.0}  # zero capacity

    kpis = compute_kpis(
        costs={},
        demand=demand,
        fulfilled=fulfilled,
        plant_production=plant_production,
        plant_capacity=plant_capacity,
    )

    util = kpis["capacity_utilization"]
    # Both should be 0.0 and not raise
    assert math.isclose(util["P1"], 0.0, rel_tol=1e-12)
    assert math.isclose(util["P2"], 0.0, rel_tol=1e-12)


def test_kpi_floating_point_stability():
    # Construct a case where floating point rounding could bite
    costs = {"production_cost": 0.1 + 0.2}  # 0.30000000000000004 typical FP
    demand = {
        ("C1", "t1"): 0.1,
        ("C1", "t2"): 0.2,
    }
    fulfilled = {
        ("C1", "t1"): 0.1,
        ("C1", "t2"): 0.2,
    }

    kpis = compute_kpis(
        costs=costs,
        demand=demand,
        fulfilled=fulfilled,
        plant_production={},
        plant_capacity={},
    )

    # Cost is preserved, but we compare tolerantly
    assert math.isclose(kpis["production_cost"], 0.3, rel_tol=1e-9)
    assert math.isclose(kpis["total_cost"], 0.3, rel_tol=1e-9)

    # Service level should be exactly 1.0 within tolerance
    assert math.isclose(kpis["service_level"], 1.0, rel_tol=1e-9)

    # No stockouts
    assert math.isclose(kpis["stockout_risk"], 0.0, rel_tol=1e-9)
