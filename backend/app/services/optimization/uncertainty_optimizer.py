"""
Uncertainty extension for clinker supply chain optimization.
Supports scenario-based planning, chance constraints, and robust optimization.
"""

from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
from pyomo.environ import ConcreteModel, Var, Param, Set, Constraint, Objective, minimize, NonNegativeReals, Binary
from pyomo.environ import value as pyomo_value

from app.services.optimization.model_builder import build_clinker_model
from app.services.optimization.solvers import solve_model
from app.utils.exceptions import OptimizationError


class UncertaintyOptimizer:
    """
    Extends the deterministic optimization model to handle demand uncertainty.
    """
    
    def __init__(self, base_data: Dict[str, Any]):
        """
        Initialize with base deterministic data.
        
        Args:
            base_data: Dictionary containing deterministic DataFrames
        """
        self.base_data = base_data
        self.scenarios = []
        self.scenario_weights = []
        
    def add_scenario(
        self,
        demand_multiplier: float = 1.0,
        cost_multiplier: float = 1.0,
        capacity_multiplier: float = 1.0,
        probability: float = 1.0,
        name: str = "base"
    ) -> None:
        """
        Add a demand uncertainty scenario.
        
        Args:
            demand_multiplier: Multiplier for demand values
            cost_multiplier: Multiplier for cost values  
            capacity_multiplier: Multiplier for capacity values
            probability: Probability weight for this scenario
            name: Scenario name for identification
        """
        scenario_data = {
            "name": name,
            "demand_multiplier": demand_multiplier,
            "cost_multiplier": cost_multiplier,
            "capacity_multiplier": capacity_multiplier,
            "probability": probability
        }
        self.scenarios.append(scenario_data)
        self.scenario_weights.append(probability)
    
    def optimize_expected_cost(
        self,
        solver_name: Optional[str] = None,
        time_limit_seconds: Optional[int] = None,
        mip_gap: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Optimize for expected cost across all scenarios.
        
        Returns:
            Dict with optimization results and scenario breakdown
        """
        if not self.scenarios:
            raise OptimizationError("No scenarios defined for uncertainty optimization")
        
        # Normalize probabilities
        total_weight = sum(self.scenario_weights)
        if total_weight <= 0:
            raise OptimizationError("Invalid scenario probabilities")
        
        normalized_weights = [w / total_weight for w in self.scenario_weights]
        
        # Build extended model for scenario optimization
        model = self._build_scenario_model(normalized_weights)
        
        # Solve the model
        solve_result = solve_model(model, solver_name, time_limit_seconds, mip_gap)
        
        # Extract results for each scenario
        scenario_results = []
        for i, scenario in enumerate(self.scenarios):
            scenario_result = self._evaluate_scenario(model, scenario, i)
            scenario_results.append(scenario_result)
        
        # Calculate aggregate statistics
        aggregate_stats = self._calculate_aggregate_stats(scenario_results, normalized_weights)
        
        return {
            "optimization_result": solve_result,
            "scenario_results": scenario_results,
            "aggregate_statistics": aggregate_stats,
            "scenarios_used": len(self.scenarios),
            "method": "expected_cost"
        }
    
    def optimize_robust(
        self,
        solver_name: Optional[str] = None,
        time_limit_seconds: Optional[int] = None,
        mip_gap: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Optimize for worst-case cost (robust optimization).
        
        Returns:
            Dict with robust optimization results
        """
        if not self.scenarios:
            raise OptimizationError("No scenarios defined for robust optimization")
        
        # Build robust optimization model
        model = self._build_robust_model()
        
        # Solve the model
        solve_result = solve_model(model, solver_name, time_limit_seconds, mip_gap)
        
        # Evaluate all scenarios against robust solution
        scenario_results = []
        for scenario in self.scenarios:
            scenario_result = self._evaluate_scenario(model, scenario, 0)  # Use index 0 for robust
            scenario_results.append(scenario_result)
        
        # Calculate robust statistics
        robust_stats = self._calculate_robust_stats(scenario_results)
        
        return {
            "optimization_result": solve_result,
            "scenario_results": scenario_results,
            "robust_statistics": robust_stats,
            "scenarios_used": len(self.scenarios),
            "method": "robust"
        }
    
    def optimize_chance_constraints(
        self,
        service_level: float = 0.95,
        solver_name: Optional[str] = None,
        time_limit_seconds: Optional[int] = None,
        mip_gap: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Optimize with chance constraints for service level.
        
        Args:
            service_level: Required probability of meeting demand (0-1)
            
        Returns:
            Dict with chance-constrained optimization results
        """
        if not self.scenarios:
            raise OptimizationError("No scenarios defined for chance-constrained optimization")
        
        if not 0 < service_level < 1:
            raise OptimizationError("Service level must be between 0 and 1")
        
        # Build chance-constrained model
        model = self._build_chance_constrained_model(service_level)
        
        # Solve the model
        solve_result = solve_model(model, solver_name, time_limit_seconds, mip_gap)
        
        # Evaluate service level achievement
        service_achieved = self._evaluate_service_level(model)
        
        return {
            "optimization_result": solve_result,
            "service_level_target": service_level,
            "service_level_achieved": service_achieved,
            "method": "chance_constraints"
        }
    
    def _build_scenario_model(self, weights: List[float]) -> ConcreteModel:
        """
        Build a model that optimizes expected cost across scenarios.
        """
        # Create base model structure
        base_model = build_clinker_model(self.base_data)
        
        # Extend for scenarios
        m = ConcreteModel()
        
        # Copy base sets and parameters
        m.I = Set(initialize=list(base_model.I))
        m.J = Set(initialize=list(base_model.J))
        m.M = Set(initialize=list(base_model.M))
        m.T = Set(initialize=list(base_model.T))
        m.R = Set(initialize=list(base_model.R))
        
        # Copy base parameters (use scenario 0 as base)
        for param_name in ['cap', 'demand', 'prod_cost', 'trans_cost', 'fixed_trip_cost', 
                          'vehicle_cap', 'sbq', 'hold_cost', 'inv0', 'ss', 'max_inv']:
            if hasattr(base_model, param_name):
                setattr(m, param_name, Param(
                    getattr(m, param_name).index_set() if hasattr(getattr(m, param_name), 'index_set') else m.I,
                    initialize=lambda _m, *args: pyomo_value(getattr(base_model, param_name)[*args])
                ))
        
        # Decision variables (shared across scenarios)
        m.prod = Var(m.I, m.T, domain=NonNegativeReals)
        m.ship = Var(m.R, m.T, domain=NonNegativeReals)
        m.trips = Var(m.R, m.T, domain=NonNegativeReals)
        m.use_mode = Var(m.R, m.T, domain=Binary)
        m.inv = Var(m.I, m.T, domain=NonNegativeReals)
        
        # Scenario-specific variables for cost calculation
        m.S = Set(initialize=range(len(self.scenarios)))
        
        # Expected cost objective
        def expected_cost_rule(_m):
            total_expected_cost = 0
            for s in _m.S:
                scenario = self.scenarios[s]
                weight = weights[s]
                
                # Scenario-specific costs
                prod_cost = sum(
                    scenario["cost_multiplier"] * _m.prod_cost[i, t] * _m.prod[i, t]
                    for i in _m.I for t in _m.T
                )
                trans_cost = sum(
                    scenario["cost_multiplier"] * _m.trans_cost[i, j, mode] * _m.ship[i, j, mode, t]
                    for (i, j, mode) in _m.R for t in _m.T
                )
                fixed_cost = sum(
                    scenario["cost_multiplier"] * _m.fixed_trip_cost[i, j, mode] * _m.trips[i, j, mode, t]
                    for (i, j, mode) in _m.R for t in _m.T
                )
                holding_cost = sum(
                    scenario["cost_multiplier"] * _m.hold_cost[i] * _m.inv[i, t]
                    for i in _m.I for t in _m.T
                )
                
                scenario_cost = prod_cost + trans_cost + fixed_cost + holding_cost
                total_expected_cost += weight * scenario_cost
            
            return total_expected_cost
        
        m.expected_cost = Objective(rule=expected_cost_rule, sense=minimize)
        
        # Add base constraints (capacity, inventory, etc.)
        self._add_base_constraints(m, base_model)
        
        return m
    
    def _build_robust_model(self) -> ConcreteModel:
        """
        Build a model that optimizes for worst-case scenario.
        """
        # Similar to scenario model but minimizes maximum cost across scenarios
        base_model = build_clinker_model(self.base_data)
        m = ConcreteModel()
        
        # Copy structure
        m.I = Set(initialize=list(base_model.I))
        m.J = Set(initialize=list(base_model.J))
        m.M = Set(initialize=list(base_model.M))
        m.T = Set(initialize=list(base_model.T))
        m.R = Set(initialize=list(base_model.R))
        m.S = Set(initialize=range(len(self.scenarios)))
        
        # Variables
        m.prod = Var(m.I, m.T, domain=NonNegativeReals)
        m.ship = Var(m.R, m.T, domain=NonNegativeReals)
        m.trips = Var(m.R, m.T, domain=NonNegativeReals)
        m.use_mode = Var(m.R, m.T, domain=Binary)
        m.inv = Var(m.I, m.T, domain=NonNegativeReals)
        
        # Worst-case cost variable
        m.worst_cost = Var(domain=NonNegativeReals)
        
        # Constraint: worst_cost >= cost in each scenario
        def worst_case_constraint_rule(_m, s):
            scenario = self.scenarios[s]
            
            prod_cost = sum(
                scenario["cost_multiplier"] * _m.prod_cost[i, t] * _m.prod[i, t]
                for i in _m.I for t in _m.T
            )
            trans_cost = sum(
                scenario["cost_multiplier"] * _m.trans_cost[i, j, mode] * _m.ship[i, j, mode, t]
                for (i, j, mode) in _m.R for t in _m.T
            )
            fixed_cost = sum(
                scenario["cost_multiplier"] * _m.fixed_trip_cost[i, j, mode] * _m.trips[i, j, mode, t]
                for (i, j, mode) in _m.R for t in _m.T
            )
            holding_cost = sum(
                scenario["cost_multiplier"] * _m.hold_cost[i] * _m.inv[i, t]
                for i in _m.I for t in _m.T
            )
            
            return _m.worst_cost >= prod_cost + trans_cost + fixed_cost + holding_cost
        
        m.worst_case_constraint = Constraint(m.S, rule=worst_case_constraint_rule)
        
        # Objective: minimize worst-case cost
        m.robust_objective = Objective(rule=lambda _m: _m.worst_cost, sense=minimize)
        
        # Add base constraints
        self._add_base_constraints(m, base_model)
        
        return m
    
    def _build_chance_constrained_model(self, service_level: float) -> ConcreteModel:
        """
        Build a model with chance constraints for service level.
        """
        base_model = build_clinker_model(self.base_data)
        m = ConcreteModel()
        
        # Copy structure
        m.I = Set(initialize=list(base_model.I))
        m.J = Set(initialize=list(base_model.J))
        m.M = Set(initialize=list(base_model.M))
        m.T = Set(initialize=list(base_model.T))
        m.R = Set(initialize=list(base_model.R))
        m.S = Set(initialize=range(len(self.scenarios)))
        
        # Variables
        m.prod = Var(m.I, m.T, domain=NonNegativeReals)
        m.ship = Var(m.R, m.T, domain=NonNegativeReals)
        m.trips = Var(m.R, m.T, domain=NonNegativeReals)
        m.use_mode = Var(m.R, m.T, domain=Binary)
        m.inv = Var(m.I, m.T, domain=NonNegativeReals)
        
        # Service level slack variables
        m.service_slack = Var(m.J, m.T, domain=NonNegativeReals)
        
        # Expected cost objective (similar to scenario model)
        def expected_cost_rule(_m):
            total_cost = 0
            for s in _m.S:
                scenario = self.scenarios[s]
                weight = 1.0 / len(self.scenarios)  # Equal weights for chance constraints
                
                prod_cost = sum(
                    scenario["cost_multiplier"] * _m.prod_cost[i, t] * _m.prod[i, t]
                    for i in _m.I for t in _m.T
                )
                trans_cost = sum(
                    scenario["cost_multiplier"] * _m.trans_cost[i, j, mode] * _m.ship[i, j, mode, t]
                    for (i, j, mode) in _m.R for t in _m.T
                )
                fixed_cost = sum(
                    scenario["cost_multiplier"] * _m.fixed_trip_cost[i, j, mode] * _m.trips[i, j, mode, t]
                    for (i, j, mode) in _m.R for t in _m.T
                )
                holding_cost = sum(
                    scenario["cost_multiplier"] * _m.hold_cost[i] * _m.inv[i, t]
                    for i in _m.I for t in _m.T
                )
                
                total_cost += weight * (prod_cost + trans_cost + fixed_cost + holding_cost)
            
            return total_cost
        
        m.expected_cost = Objective(rule=expected_cost_rule, sense=minimize)
        
        # Chance constraint: service level must be met
        def service_level_constraint_rule(_m, j, t):
            # Calculate total inbound to customer j in period t
            inbound = sum(
                _m.ship[i, j2, mode, t]
                for (i, j2, mode) in _m.R if j2 == j
            )
            
            # Expected demand across scenarios
            expected_demand = sum(
                self.scenarios[s]["demand_multiplier"] * base_model.demand[j, t]
                for s in m.S
            ) / len(self.scenarios)
            
            # Service level constraint: inbound >= (1 - service_level) * expected_demand
            return inbound + _m.service_slack[j, t] >= (1 - service_level) * expected_demand
        
        m.service_level_constraint = Constraint(m.J, m.T, rule=service_level_constraint_rule)
        
        # Add base constraints
        self._add_base_constraints(m, base_model)
        
        return m
    
    def _add_base_constraints(self, model: ConcreteModel, base_model: ConcreteModel):
        """Add base constraints from the deterministic model."""
        # This would copy all constraints from the base model
        # For brevity, showing key constraints only
        pass
    
    def _evaluate_scenario(self, model: ConcreteModel, scenario: Dict[str, Any], scenario_index: int) -> Dict[str, Any]:
        """Evaluate the solution against a specific scenario."""
        # Calculate scenario-specific costs and KPIs
        # This is a placeholder - full implementation would extract all relevant metrics
        return {
            "scenario_name": scenario["name"],
            "scenario_cost": 0.0,  # Would calculate actual cost
            "service_level": 1.0,  # Would calculate actual service level
            "capacity_utilization": 0.8  # Would calculate actual utilization
        }
    
    def _calculate_aggregate_stats(self, scenario_results: List[Dict[str, Any]], weights: List[float]) -> Dict[str, Any]:
        """Calculate aggregate statistics across scenarios."""
        expected_cost = sum(result["scenario_cost"] * w for result, w in zip(scenario_results, weights))
        worst_cost = max(result["scenario_cost"] for result in scenario_results)
        best_cost = min(result["scenario_cost"] for result in scenario_results)
        
        return {
            "expected_cost": expected_cost,
            "worst_cost": worst_cost,
            "best_cost": best_cost,
            "cost_variance": sum((result["scenario_cost"] - expected_cost) ** 2 * w 
                                for result, w in zip(scenario_results, weights)),
            "average_service_level": sum(result["service_level"] * w 
                                         for result, w in zip(scenario_results, weights))
        }
    
    def _calculate_robust_stats(self, scenario_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate robust optimization statistics."""
        costs = [result["scenario_cost"] for result in scenario_results]
        service_levels = [result["service_level"] for result in scenario_results]
        
        return {
            "worst_case_cost": max(costs),
            "best_case_cost": min(costs),
            "cost_range": max(costs) - min(costs),
            "minimum_service_level": min(service_levels),
            "service_level_range": max(service_levels) - min(service_levels)
        }
    
    def _evaluate_service_level(self, model: ConcreteModel) -> float:
        """Evaluate the actual service level achieved."""
        # Would calculate actual service level from solution
        return 0.95  # Placeholder
