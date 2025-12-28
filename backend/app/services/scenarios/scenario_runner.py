from typing import Any, Dict, List

import pandas as pd

from app.services.kpi_calculator import compute_kpis as compute_kpis_core
from app.services.optimization.model_builder import build_clinker_model
from app.services.optimization.result_parser import extract_solution
from app.services.optimization.solvers import solve_model
from app.services.scenarios.scenario_generator import ScenarioConfig, ScenarioType, generate_demand_for_scenario
from app.utils.exceptions import OptimizationError


def _compute_kpis_from_solution(solution: Dict[str, Any]) -> Dict[str, Any]:
	"""Adapter that feeds solver outputs into the shared KPI calculator.

	The solver/optimizer is free to choose its own internal structures as long
	as it exposes the aggregate data required by compute_kpis via a simple
	"solution" mapping. Missing keys default to empty mappings, which the
	shared KPI calculator treats as zeros.
	"""
	return compute_kpis_core(
		costs=solution.get("costs", {}) or {},
		demand=solution.get("demand", {}) or {},
		fulfilled=solution.get("fulfilled", {}) or {},
		plant_production=solution.get("plant_production", {}) or {},
		plant_capacity=solution.get("plant_capacity", {}) or {},
	)


def _build_model_input_for_scenario(
	data: Dict[str, pd.DataFrame],
	scenario_cfg: ScenarioConfig,
	demand_df: pd.DataFrame,
) -> Dict[str, Any]:
	"""Clone base model input and replace demand_forecast with scenario-specific demand.

	`data` is expected to contain the cleaned DataFrames used by the optimizer:
	- plants
	- production_capacity_cost
	- transport_routes_modes
	- demand_forecast (will be replaced)
	- safety_stock_policy (optional)
	- initial_inventory (optional)
	- time_periods (optional list)
	"""

	model_input: Dict[str, Any] = {
		"plants": data["plants"],
		"production_capacity_cost": data["production_capacity_cost"],
		"transport_routes_modes": data["transport_routes_modes"],
		"demand_forecast": demand_df,
		"safety_stock_policy": data.get("safety_stock_policy", pd.DataFrame()),
		"initial_inventory": data.get("initial_inventory", pd.DataFrame()),
		"time_periods": data.get("time_periods"),
	}
	# Attach scenario metadata for downstream reporting
	model_input["scenario_name"] = scenario_cfg.name
	model_input["scenario_type"] = scenario_cfg.type
	return model_input


def run_single_scenario_from_config(
	data: Dict[str, pd.DataFrame],
	scenario_cfg: ScenarioConfig,
	solver_name: str = "highs",
) -> Dict[str, Any]:
	"""Run a single scenario from config and base data.

	Returns a JSON-serializable dict containing solver status, KPIs, and
	solution details. If the scenario is infeasible or solver fails, returns a
	status and error instead of throwing.
	"""

	base_demand_df: pd.DataFrame = data["demand_forecast"]
	try:
		scenario_demand_df = generate_demand_for_scenario(base_demand_df, scenario_cfg)
	except OptimizationError as e:
		return {
			"name": scenario_cfg.name,
			"type": scenario_cfg.type,
			"status": "invalid_scenario",
			"error": str(e),
		}

	model_input = _build_model_input_for_scenario(data, scenario_cfg, scenario_demand_df)

	try:
		model = build_clinker_model(model_input)
		solver_meta = solve_model(model, solver_name=solver_name)
		solution = extract_solution(model)
		# Compute KPIs via the shared calculator; scenario engine remains orchestrator.
		kpis = _compute_kpis_from_solution(solution)
		return {
			"name": scenario_cfg.name,
			"type": scenario_cfg.type,
			"status": "completed",
			"solver_status": solver_meta.get("status"),
			"solver_termination": solver_meta.get("termination"),
			"solver": solver_meta.get("solver"),
			"kpis": kpis,
			"solution": solution,
		}
	except OptimizationError as e:
		return {
			"name": scenario_cfg.name,
			"type": scenario_cfg.type,
			"status": "failed",
			"error": str(e),
		}
	except Exception as e:
		return {
			"name": scenario_cfg.name,
			"type": scenario_cfg.type,
			"status": "failed",
			"error": f"Unexpected error: {e}",
		}


def run_batch_scenarios_from_configs(
	data: Dict[str, pd.DataFrame],
	scenarios: List[ScenarioConfig],
	solver_name: str = "highs",
) -> Dict[str, Any]:
	"""Execute multiple scenarios sequentially and return a JSON-compatible structure.

	Parameters
	----------
	data:
		Cleaned DataFrames required by the optimization engine.
	scenarios:
		List of ScenarioConfig objects specifying how to perturb demand.
	solver_name:
		MILP solver to use (defaults to "highs").

	Returns
	-------
	Dict[str, Any]
		{"scenarios": [...]} where each entry includes metadata, KPIs, and solution.
	"""

	results: List[Dict[str, Any]] = []
	for cfg in scenarios:
		result = run_single_scenario_from_config(data, cfg, solver_name=solver_name)
		results.append(result)

	return {"scenarios": results}
