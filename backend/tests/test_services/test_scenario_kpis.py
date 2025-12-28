from unittest.mock import patch

import pandas as pd

from app.services.scenarios.scenario_generator import ScenarioConfig, ScenarioType
from app.services.scenarios.scenario_runner import (
    _build_model_input_for_scenario,
    run_single_scenario_from_config,
    run_batch_scenarios_from_configs,
)


def _make_base_data() -> dict:
    return {
        "plants": pd.DataFrame(),
        "production_capacity_cost": pd.DataFrame(),
        "transport_routes_modes": pd.DataFrame(),
        "demand_forecast": pd.DataFrame(
            {
                "customer_node_id": ["C1"],
                "period": ["t1"],
                "demand_tonnes": [100.0],
            }
        ),
        "safety_stock_policy": pd.DataFrame(),
        "initial_inventory": pd.DataFrame(),
        "time_periods": ["t1"],
    }


def _make_fake_solution() -> dict:
    return {
        # These aggregates are what the shared KPI calculator expects
        "costs": {
            "production_cost": 100.0,
            "transport_cost": 50.0,
            "fixed_trip_cost": 10.0,
            "holding_cost": 5.0,
        },
        "demand": {("C1", "t1"): 100.0},
        "fulfilled": {("C1", "t1"): 100.0},
        "plant_production": {"P1": 80.0},
        "plant_capacity": {"P1": 100.0},
    }


def test_scenario_result_includes_kpis_single_scenario():
    """Running a single scenario attaches a kpis dict to the result."""

    data = _make_base_data()
    cfg = ScenarioConfig(name="base", type=ScenarioType.BASE)

    fake_solution = _make_fake_solution()

    with patch("app.services.scenarios.scenario_runner.generate_demand_for_scenario", return_value=data["demand_forecast"]), patch(
        "app.services.scenarios.scenario_runner.build_clinker_model"
    ) as mock_build, patch(
        "app.services.scenarios.scenario_runner.solve_model", return_value={"status": "ok", "termination": "optimal", "solver": "mock"}
    ), patch(
        "app.services.scenarios.scenario_runner.extract_solution", return_value=fake_solution
    ), patch(
        "app.services.scenarios.scenario_runner.compute_kpis_core"
    ) as mock_compute_kpis:
        # Let the shared KPI calculator return something simple but structured
        mock_compute_kpis.return_value = {"total_cost": 165.0, "capacity_utilization": {"P1": 0.8}}

        result = run_single_scenario_from_config(data, cfg)

    assert "kpis" in result
    assert result["kpis"]["total_cost"] == 165.0
    assert result["kpis"]["capacity_utilization"]["P1"] == 0.8
    # Ensure we did not inline KPI logic: shared calculator must be called exactly once
    mock_compute_kpis.assert_called_once_with(
        costs=fake_solution["costs"],
        demand=fake_solution["demand"],
        fulfilled=fake_solution["fulfilled"],
        plant_production=fake_solution["plant_production"],
        plant_capacity=fake_solution["plant_capacity"],
    )


def test_kpis_dict_has_all_expected_keys():
    """The kpis dict includes all required KPI keys from the shared calculator."""

    data = _make_base_data()
    cfg = ScenarioConfig(name="base", type=ScenarioType.BASE)
    fake_solution = _make_fake_solution()

    full_kpis = {
        "total_cost": 1.0,
        "production_cost": 1.0,
        "transport_cost": 1.0,
        "fixed_trip_cost": 1.0,
        "holding_cost": 1.0,
        "service_level": 1.0,
        "stockout_risk": 0.0,
        "capacity_utilization": {"P1": 1.0},
    }

    with patch("app.services.scenarios.scenario_runner.generate_demand_for_scenario", return_value=data["demand_forecast"]), patch(
        "app.services.scenarios.scenario_runner.build_clinker_model"
    ), patch(
        "app.services.scenarios.scenario_runner.solve_model", return_value={"status": "ok", "termination": "optimal", "solver": "mock"}
    ), patch(
        "app.services.scenarios.scenario_runner.extract_solution", return_value=fake_solution
    ), patch(
        "app.services.scenarios.scenario_runner.compute_kpis_core", return_value=full_kpis
    ):
        result = run_single_scenario_from_config(data, cfg)

    kpis = result["kpis"]
    expected_keys = {
        "total_cost",
        "production_cost",
        "transport_cost",
        "fixed_trip_cost",
        "holding_cost",
        "service_level",
        "stockout_risk",
        "capacity_utilization",
    }
    assert set(kpis.keys()) == expected_keys


def test_multiple_scenarios_each_have_kpis():
    """When multiple scenarios are run, each result carries its own kpis."""

    data = _make_base_data()
    cfgs = [
        ScenarioConfig(name="base", type=ScenarioType.BASE),
        ScenarioConfig(name="high", type=ScenarioType.HIGH, scaling_factor=1.1),
    ]

    fake_solution = _make_fake_solution()

    with patch("app.services.scenarios.scenario_runner.generate_demand_for_scenario", return_value=data["demand_forecast"]), patch(
        "app.services.scenarios.scenario_runner.build_clinker_model"
    ), patch(
        "app.services.scenarios.scenario_runner.solve_model", return_value={"status": "ok", "termination": "optimal", "solver": "mock"}
    ), patch(
        "app.services.scenarios.scenario_runner.extract_solution", return_value=fake_solution
    ), patch(
        "app.services.scenarios.scenario_runner.compute_kpis_core", return_value={"total_cost": 1.0, "capacity_utilization": {}}
    ):
        batch_result = run_batch_scenarios_from_configs(data, cfgs)

    scenarios = batch_result["scenarios"]
    assert len(scenarios) == 2
    for scenario in scenarios:
        assert "kpis" in scenario
        assert "total_cost" in scenario["kpis"]
