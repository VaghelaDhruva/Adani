import pandas as pd
from app.services.optimization.model_builder import build_clinker_model


def test_build_clinker_model():
    """Smoke test: build the optimization model from minimal DataFrames."""

    plants = pd.DataFrame([
        {"plant_id": "P1"},
        {"plant_id": "P2"},
    ])

    production_capacity_cost = pd.DataFrame([
        {"plant_id": "P1", "period": "t1", "max_capacity_tonnes": 100.0, "variable_cost_per_tonne": 10.0},
        {"plant_id": "P2", "period": "t1", "max_capacity_tonnes": 100.0, "variable_cost_per_tonne": 12.0},
    ])

    transport_routes_modes = pd.DataFrame([
        {
            "origin_plant_id": "P1",
            "destination_node_id": "C1",
            "transport_mode": "road",
            "distance_km": 10.0,
            "cost_per_tonne": 5.0,
            "cost_per_tonne_km": None,
            "fixed_cost_per_trip": 0.0,
            "vehicle_capacity_tonnes": 100.0,
            "min_batch_quantity_tonnes": 0.0,
        },
    ])

    demand_forecast = pd.DataFrame([
        {"customer_node_id": "C1", "period": "t1", "demand_tonnes": 50.0},
    ])

    data = {
        "plants": plants,
        "production_capacity_cost": production_capacity_cost,
        "transport_routes_modes": transport_routes_modes,
        "demand_forecast": demand_forecast,
        "safety_stock_policy": pd.DataFrame(),
        "initial_inventory": pd.DataFrame(),
        "time_periods": ["t1"],
    }

    model = build_clinker_model(data)
    assert model is not None
    # Basic checks
    assert len(list(model.I)) == 2
    assert len(list(model.J)) == 1
    assert len(list(model.M)) == 1
    assert len(list(model.T)) == 1
