from app.services.scenarios.scenario_generator import generate_demand_scenarios, generate_stochastic_demand


def test_generate_demand_scenarios():
    base = [{"customer_node_id": "C1", "period": "2025-W01", "demand_tonnes": 100}]
    scenarios = generate_demand_scenarios(base, {"base": 1.0, "high": 1.2, "low": 0.8})
    assert len(scenarios) == 3
    assert scenarios[0]["scenario_name"] == "base"
    assert scenarios[1]["scenario_name"] == "high"
    assert scenarios[2]["scenario_name"] == "low"


def test_generate_stochastic_demand():
    base = [{"customer_node_id": "C1", "period": "2025-W01", "demand_tonnes": 100}]
    scenarios = generate_stochastic_demand(base, distribution="normal", std_factor=0.1)
    assert len(scenarios) == 10
    for s in scenarios:
        assert s["scenario_name"].startswith("stochastic_")
        assert len(s["demand"]) == 1
