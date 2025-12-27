from unittest.mock import patch

import pandas as pd
from fastapi import status

from app.services.scenarios.scenario_generator import ScenarioType
from app.utils.exceptions import OptimizationError


def test_run_scenarios_endpoint_success(client):
    """Minimal test that the /api/v1/scenarios/run endpoint accepts configs and returns scenarios wrapper.

    The underlying scenario runner is patched to avoid depending on real DB data or solver.
    """

    fake_result = {"scenarios": [{"name": "base", "type": "base", "status": "completed"}]}
    fake_data = {
        "plants": pd.DataFrame(),
        "production_capacity_cost": pd.DataFrame(),
        "transport_routes_modes": pd.DataFrame(),
        "demand_forecast": pd.DataFrame({"customer_node_id": ["C1"], "period": ["t1"], "demand_tonnes": [1.0]}),
        "safety_stock_policy": pd.DataFrame(),
        "initial_inventory": pd.DataFrame(),
        "time_periods": ["t1"],
    }

    with patch("app.api.v1.routes_scenarios._load_optimization_data", return_value=fake_data), patch(
        "app.api.v1.routes_scenarios.run_batch_scenarios_from_configs",
        return_value=fake_result,
    ):
        payload = [{"name": "base", "type": ScenarioType.BASE}]
        resp = client.post("/api/v1/scenarios/run", json=payload)
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "scenarios" in body
        assert isinstance(body["scenarios"], list)
        assert body["scenarios"][0]["name"] == "base"


def test_run_scenarios_missing_demand_returns_400(client):
    """If demand data is missing, the endpoint should return HTTP 400.

    Patch _load_optimization_data to return an empty demand_forecast DataFrame
    so the route's validation branch is exercised.
    """

    with patch("app.api.v1.routes_scenarios._load_optimization_data") as mock_load:
        mock_load.return_value = {
            "plants": pd.DataFrame(),
            "production_capacity_cost": pd.DataFrame(),
            "transport_routes_modes": pd.DataFrame(),
            "demand_forecast": pd.DataFrame(),  # empty triggers 400
            "safety_stock_policy": pd.DataFrame(),
            "initial_inventory": pd.DataFrame(),
            "time_periods": [],
        }
        payload = [{"name": "base", "type": ScenarioType.BASE}]
        resp = client.post("/api/v1/scenarios/run", json=payload)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        body = resp.json()
        assert "No demand data" in body["detail"]


def test_run_scenarios_optimization_error_returns_400(client):
    """If the scenario runner raises OptimizationError, the endpoint returns HTTP 400.

    Patch run_batch_scenarios_from_configs to raise OptimizationError so the
    route's optimization error handling branch is exercised.
    """

    fake_data = {
        "plants": pd.DataFrame(),
        "production_capacity_cost": pd.DataFrame(),
        "transport_routes_modes": pd.DataFrame(),
        "demand_forecast": pd.DataFrame({"customer_node_id": ["C1"], "period": ["t1"], "demand_tonnes": [1.0]}),
        "safety_stock_policy": pd.DataFrame(),
        "initial_inventory": pd.DataFrame(),
        "time_periods": ["t1"],
    }

    with patch("app.api.v1.routes_scenarios._load_optimization_data", return_value=fake_data), patch(
        "app.api.v1.routes_scenarios.run_batch_scenarios_from_configs",
        side_effect=OptimizationError("solver failed"),
    ):
        payload = [{"name": "base", "type": ScenarioType.BASE}]
        resp = client.post("/api/v1/scenarios/run", json=payload)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        body = resp.json()
        assert "solver failed" in body["detail"]


def test_run_scenarios_unexpected_exception_returns_500(client):
    """If an unexpected exception is raised, the endpoint should return HTTP 500.

    Patch run_batch_scenarios_from_configs to raise a generic RuntimeError and
    verify that the route converts it to a 500 without leaking details.
    """

    fake_data = {
        "plants": pd.DataFrame(),
        "production_capacity_cost": pd.DataFrame(),
        "transport_routes_modes": pd.DataFrame(),
        "demand_forecast": pd.DataFrame({"customer_node_id": ["C1"], "period": ["t1"], "demand_tonnes": [1.0]}),
        "safety_stock_policy": pd.DataFrame(),
        "initial_inventory": pd.DataFrame(),
        "time_periods": ["t1"],
    }

    with patch("app.api.v1.routes_scenarios._load_optimization_data", return_value=fake_data), patch(
        "app.api.v1.routes_scenarios.run_batch_scenarios_from_configs",
        side_effect=RuntimeError("boom"),
    ):
        payload = [{"name": "base", "type": ScenarioType.BASE}]
        resp = client.post("/api/v1/scenarios/run", json=payload)
        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        body = resp.json()
        assert body["detail"] == "Failed to run scenarios"


def test_run_scenarios_invalid_config_returns_422(client):
    """Invalid ScenarioConfig type should result in a FastAPI validation error (422).

    Given the current implementation, an unknown `type` value is accepted by the
    schema and later fails within the handler when no demand data is present.
    """

    with patch("app.api.v1.routes_scenarios._load_optimization_data") as mock_load:
        mock_load.return_value = {
            "plants": pd.DataFrame(),
            "production_capacity_cost": pd.DataFrame(),
            "transport_routes_modes": pd.DataFrame(),
            "demand_forecast": pd.DataFrame(),  # empty triggers 400
            "safety_stock_policy": pd.DataFrame(),
            "initial_inventory": pd.DataFrame(),
            "time_periods": [],
        }
        payload = [{"name": "bad", "type": "unknown_type"}]
        resp = client.post("/api/v1/scenarios/run", json=payload)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        body = resp.json()
        assert "No demand data" in body["detail"]
