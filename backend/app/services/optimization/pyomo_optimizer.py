"""
Pyomo-Based Optimization Engine

Mathematical optimization engine using Pyomo for clinker supply chain optimization.
All costs are in RAW RUPEES - no scaling or division.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pyomo.environ import (
    ConcreteModel, Var, Objective, Constraint, Set, Param,
    minimize, NonNegativeReals, Binary, Integers, value
)
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.utils.exceptions import OptimizationError, DataValidationError

logger = logging.getLogger(__name__)
settings = get_settings()


class PyomoOptimizer:
    """Pyomo-based optimization engine for supply chain optimization."""
    
    def __init__(self):
        self.model = None
        self.solution_data = {}
        self.objective_value = None
        
    def build_model(self, input_data: Dict[str, Any], db: Session) -> None:
        """
        Build the Pyomo optimization model.
        
        All costs must be in RAW RUPEES:
        - Production: ₹/ton
        - Transport variable: ₹/ton OR ₹/ton-km (not both)
        - Fixed trip: ₹/trip
        - Inventory: ₹/ton-period
        - Penalty: ₹/ton
        """
        try:
            logger.info("Building Pyomo optimization model")
            
            # Extract data components
            plants = input_data.get("plants", [])
            customers = input_data.get("customers", [])
            periods = input_data.get("periods", [])
            transport_modes = input_data.get("transport_modes", [])
            routes = input_data.get("routes", [])
            demand = input_data.get("demand", [])
            costs = input_data.get("costs", {})
            
            # Validate input data
            self._validate_input_data(input_data)
            
            # Create Pyomo model
            self.model = ConcreteModel()
            
            # Create sets
            self._create_sets(plants, customers, periods, transport_modes, routes)
            
            # Create parameters
            self._create_parameters(input_data, costs)
            
            # Create decision variables
            self._create_variables()
            
            # Create objective function
            self._create_objective(costs)
            
            # Create constraints
            self._create_constraints(input_data)
            
            logger.info(f"Pyomo model built: {len(self.model.component_objects(Var))} variable sets, "
                       f"{len(self.model.component_objects(Constraint))} constraint sets")
            
        except Exception as e:
            logger.error(f"Error building Pyomo model: {e}", exc_info=True)
            raise OptimizationError(f"Model building failed: {str(e)}")
    
    def _validate_input_data(self, input_data: Dict[str, Any]) -> None:
        """Validate input data for optimization."""
        required_keys = ["plants", "customers", "periods", "demand", "costs"]
        
        for key in required_keys:
            if key not in input_data:
                raise DataValidationError(f"Missing required input data: {key}")
        
        # Validate cost units are in RUPEES
        costs = input_data.get("costs", {})
        
        # Check for any division by 1000 or scaling factors
        for cost_type, cost_data in costs.items():
            if isinstance(cost_data, dict):
                for key, value in cost_data.items():
                    if isinstance(value, (int, float)) and value < 1:
                        logger.warning(f"Cost value {value} for {cost_type}/{key} seems unusually low. "
                                     f"Ensure all costs are in RAW RUPEES, not scaled.")
        
        logger.info("Input data validation passed")
    
    def _create_sets(self, plants: List[Dict], customers: List[Dict], 
                    periods: List[str], transport_modes: List[Dict], 
                    routes: List[Dict]) -> None:
        """Create Pyomo sets."""
        
        # Plant set
        plant_ids = [p["plant_id"] for p in plants]
        self.model.PLANTS = Set(initialize=plant_ids)
        
        # Customer/GU set
        customer_ids = [c["customer_id"] for c in customers]
        self.model.CUSTOMERS = Set(initialize=customer_ids)
        
        # Period set
        self.model.PERIODS = Set(initialize=periods, ordered=True)
        
        # Transport mode set
        mode_names = [m["mode"] for m in transport_modes]
        self.model.MODES = Set(initialize=mode_names)
        
        # Route set (from, to, mode)
        route_tuples = [
            (r["from"], r["to"], r["mode"]) 
            for r in routes
        ]
        self.model.ROUTES = Set(initialize=route_tuples, dimen=3)
        
        logger.info(f"Created sets: {len(plant_ids)} plants, {len(customer_ids)} customers, "
                   f"{len(periods)} periods, {len(mode_names)} modes, {len(route_tuples)} routes")
    
    def _create_parameters(self, input_data: Dict[str, Any], costs: Dict[str, Any]) -> None:
        """Create Pyomo parameters."""
        
        plants = input_data["plants"]
        routes = input_data["routes"]
        demand = input_data["demand"]
        transport_modes = input_data["transport_modes"]
        
        # Production capacity (tons per period)
        capacity_dict = {}
        for plant in plants:
            for period in self.model.PERIODS:
                capacity_dict[(plant["plant_id"], period)] = plant.get("capacity_tonnes", 0)
        self.model.PROD_CAPACITY = Param(self.model.PLANTS, self.model.PERIODS, 
                                         initialize=capacity_dict, default=0)
        
        # Production cost (₹/ton) - RAW RUPEES
        prod_cost_dict = {}
        for plant in plants:
            plant_id = plant["plant_id"]
            # Get from costs dict or use default
            unit_cost = costs.get("production", {}).get(plant_id, 1850.0)
            for period in self.model.PERIODS:
                prod_cost_dict[(plant_id, period)] = float(unit_cost)
        self.model.PROD_COST = Param(self.model.PLANTS, self.model.PERIODS,
                                     initialize=prod_cost_dict, default=1850.0)
        
        # Demand (tons per period)
        demand_dict = {}
        for d in demand:
            key = (d["customer_id"], d["period"])
            demand_dict[key] = float(d["demand_tonnes"])
        self.model.DEMAND = Param(self.model.CUSTOMERS, self.model.PERIODS,
                                  initialize=demand_dict, default=0.0)
        
        # Transport variable cost (₹/ton) - RAW RUPEES
        transport_cost_dict = {}
        for route in routes:
            route_key = f"{route['from']}_{route['to']}_{route['mode']}"
            unit_cost = costs.get("transport", {}).get(route_key, 250.0)
            transport_cost_dict[(route["from"], route["to"], route["mode"])] = float(unit_cost)
        self.model.TRANSPORT_COST = Param(self.model.ROUTES,
                                         initialize=transport_cost_dict, default=250.0)
        
        # Fixed trip cost (₹/trip) - RAW RUPEES
        fixed_cost_dict = {}
        for route in routes:
            route_key = f"{route['from']}_{route['to']}_{route['mode']}"
            fixed_cost = costs.get("fixed_transport", {}).get(route_key, 5000.0)
            fixed_cost_dict[(route["from"], route["to"], route["mode"])] = float(fixed_cost)
        self.model.FIXED_TRIP_COST = Param(self.model.ROUTES,
                                           initialize=fixed_cost_dict, default=5000.0)
        
        # Vehicle capacity (tons per trip)
        vehicle_capacity_dict = {}
        for route in routes:
            mode = route["mode"]
            # Find capacity for this mode
            capacity = 30.0  # Default
            for tm in transport_modes:
                if tm["mode"] == mode:
                    capacity = float(tm.get("capacity_tonnes", 30.0))
                    break
            vehicle_capacity_dict[(route["from"], route["to"], route["mode"])] = capacity
        self.model.VEHICLE_CAPACITY = Param(self.model.ROUTES,
                                           initialize=vehicle_capacity_dict, default=30.0)
        
        # SBQ (Shipment Batch Quantity) - minimum shipment size
        sbq_dict = {}
        for route in routes:
            route_key = f"{route['from']}_{route['to']}_{route['mode']}"
            sbq = costs.get("sbq", {}).get(route_key, 0.0)
            sbq_dict[(route["from"], route["to"], route["mode"])] = float(sbq)
        self.model.SBQ = Param(self.model.ROUTES, initialize=sbq_dict, default=0.0)
        
        # Inventory holding cost (₹/ton-period) - RAW RUPEES
        holding_cost_dict = {}
        for plant in plants:
            plant_id = plant["plant_id"]
            holding_cost = costs.get("inventory", {}).get(plant_id, 15.0)
            for period in self.model.PERIODS:
                holding_cost_dict[(plant_id, period)] = float(holding_cost)
        self.model.HOLDING_COST = Param(self.model.PLANTS, self.model.PERIODS,
                                        initialize=holding_cost_dict, default=15.0)
        
        # Penalty cost for unmet demand (₹/ton) - RAW RUPEES
        penalty_cost = costs.get("penalty", {}).get("unmet_demand", 10000.0)
        self.model.PENALTY_COST = Param(initialize=float(penalty_cost), default=10000.0)
        
        # Initial inventory
        initial_inv_dict = {}
        for plant in plants:
            initial_inv_dict[plant["plant_id"]] = float(plant.get("initial_inventory", 0.0))
        self.model.INITIAL_INVENTORY = Param(self.model.PLANTS,
                                           initialize=initial_inv_dict, default=0.0)
        
        # Safety stock
        safety_stock_dict = {}
        for plant in plants:
            for period in self.model.PERIODS:
                safety_stock_dict[(plant["plant_id"], period)] = float(
                    plant.get("safety_stock_tonnes", 0.0)
                )
        self.model.SAFETY_STOCK = Param(self.model.PLANTS, self.model.PERIODS,
                                       initialize=safety_stock_dict, default=0.0)
        
        # Max storage capacity
        max_storage_dict = {}
        for plant in plants:
            for period in self.model.PERIODS:
                max_storage_dict[(plant["plant_id"], period)] = float(
                    plant.get("max_storage_tonnes", 1000000.0)
                )
        self.model.MAX_STORAGE = Param(self.model.PLANTS, self.model.PERIODS,
                                      initialize=max_storage_dict, default=1000000.0)
    
    def _create_variables(self) -> None:
        """Create Pyomo decision variables."""
        
        # Production: X[p, t] = tons produced at plant p in period t
        self.model.X = Var(self.model.PLANTS, self.model.PERIODS,
                          domain=NonNegativeReals, name="production")
        
        # Shipment: Y[from, to, mode, t] = tons shipped from origin to destination via mode in period t
        self.model.Y = Var(self.model.ROUTES, self.model.PERIODS,
                          domain=NonNegativeReals, name="shipment")
        
        # Inventory: I[p, t] = tons in inventory at plant p at end of period t
        self.model.I = Var(self.model.PLANTS, self.model.PERIODS,
                          domain=NonNegativeReals, name="inventory")
        
        # Integer trips: T[from, to, mode, t] = number of trips (INTEGER)
        self.model.T = Var(self.model.ROUTES, self.model.PERIODS,
                          domain=Integers, name="trips")
        
        # Binary activation: Z[from, to, mode, t] = 1 if route is used, 0 otherwise
        self.model.Z = Var(self.model.ROUTES, self.model.PERIODS,
                          domain=Binary, name="route_activation")
        
        # Unmet demand: U[c, t] = tons of unmet demand for customer c in period t
        self.model.U = Var(self.model.CUSTOMERS, self.model.PERIODS,
                          domain=NonNegativeReals, name="unmet_demand")
        
        logger.info("Decision variables created")
    
    def _create_objective(self, costs: Dict[str, Any]) -> None:
        """
        Create objective function: minimize total cost.
        
        Total cost = Production + Variable Transport + Fixed Trip + Holding + Penalty
        All in RAW RUPEES.
        """
        
        # Production cost
        production_cost = sum(
            self.model.X[p, t] * self.model.PROD_COST[p, t]
            for p in self.model.PLANTS
            for t in self.model.PERIODS
        )
        
        # Variable transport cost
        transport_cost = sum(
            self.model.Y[r, t] * self.model.TRANSPORT_COST[r]
            for r in self.model.ROUTES
            for t in self.model.PERIODS
        )
        
        # Fixed trip cost
        fixed_trip_cost = sum(
            self.model.T[r, t] * self.model.FIXED_TRIP_COST[r]
            for r in self.model.ROUTES
            for t in self.model.PERIODS
        )
        
        # Inventory holding cost
        holding_cost = sum(
            self.model.I[p, t] * self.model.HOLDING_COST[p, t]
            for p in self.model.PLANTS
            for t in self.model.PERIODS
        )
        
        # Penalty cost for unmet demand
        penalty_cost = sum(
            self.model.U[c, t] * self.model.PENALTY_COST
            for c in self.model.CUSTOMERS
            for t in self.model.PERIODS
        )
        
        # Total objective
        total_cost = (production_cost + transport_cost + fixed_trip_cost + 
                     holding_cost + penalty_cost)
        
        self.model.objective = Objective(expr=total_cost, sense=minimize)
        
        logger.info("Objective function created: minimize total cost (all in RAW RUPEES)")
    
    def _create_constraints(self, input_data: Dict[str, Any]) -> None:
        """Create optimization constraints."""
        
        # 1. Production capacity constraints
        def production_capacity_rule(model, p, t):
            return model.X[p, t] <= model.PROD_CAPACITY[p, t]
        self.model.prod_capacity_constraint = Constraint(
            self.model.PLANTS, self.model.PERIODS, rule=production_capacity_rule
        )
        
        # 2. Inventory balance constraints
        def inventory_balance_rule(model, p, t):
            periods_list = list(model.PERIODS)
            t_idx = periods_list.index(t)
            
            if t_idx == 0:
                # First period: opening inventory + production - outbound = closing inventory
                opening_inv = model.INITIAL_INVENTORY[p]
            else:
                # Subsequent periods: previous period's closing inventory
                prev_t = periods_list[t_idx - 1]
                opening_inv = model.I[p, prev_t]
            
            # Production in this period
            production = model.X[p, t]
            
            # Outbound shipments from this plant in this period
            outbound = sum(
                model.Y[r, t]
                for r in model.ROUTES
                if r[0] == p  # Route origin is this plant
            )
            
            # Closing inventory
            closing_inv = model.I[p, t]
            
            return opening_inv + production == outbound + closing_inv
        
        self.model.inventory_balance_constraint = Constraint(
            self.model.PLANTS, self.model.PERIODS, rule=inventory_balance_rule
        )
        
        # 3. Demand satisfaction constraints
        def demand_satisfaction_rule(model, c, t):
            # Inbound shipments to this customer
            inbound = sum(
                model.Y[r, t]
                for r in model.ROUTES
                if r[1] == c  # Route destination is this customer
            )
            
            # Unmet demand
            unmet = model.U[c, t]
            
            # Demand requirement
            return inbound + unmet >= model.DEMAND[c, t]
        
        self.model.demand_satisfaction_constraint = Constraint(
            self.model.CUSTOMERS, self.model.PERIODS, rule=demand_satisfaction_rule
        )
        
        # 4. Safety stock constraints
        def safety_stock_rule(model, p, t):
            return model.I[p, t] >= model.SAFETY_STOCK[p, t]
        self.model.safety_stock_constraint = Constraint(
            self.model.PLANTS, self.model.PERIODS, rule=safety_stock_rule
        )
        
        # 5. Maximum storage constraints
        def max_storage_rule(model, p, t):
            return model.I[p, t] <= model.MAX_STORAGE[p, t]
        self.model.max_storage_constraint = Constraint(
            self.model.PLANTS, self.model.PERIODS, rule=max_storage_rule
        )
        
        # 6. Trip capacity constraints: shipment <= trips × vehicle capacity
        def trip_capacity_rule(model, r, t):
            return model.Y[r, t] <= model.T[r, t] * model.VEHICLE_CAPACITY[r]
        self.model.trip_capacity_constraint = Constraint(
            self.model.ROUTES, self.model.PERIODS, rule=trip_capacity_rule
        )
        
        # 7. SBQ constraints: if shipped, then shipment >= SBQ
        def sbq_rule(model, r, t):
            # Big M constraint: Y[r, t] >= SBQ[r] * Z[r, t]
            # If Z[r, t] = 1, then Y[r, t] >= SBQ[r]
            # If Z[r, t] = 0, then Y[r, t] >= 0 (non-binding)
            big_m = 1000000.0  # Large number
            return model.Y[r, t] >= model.SBQ[r] * model.Z[r, t]
        self.model.sbq_constraint = Constraint(
            self.model.ROUTES, self.model.PERIODS, rule=sbq_rule
        )
        
        # 8. Route activation constraints: if shipment > 0, then Z = 1
        def route_activation_rule(model, r, t):
            big_m = 1000000.0
            return model.Y[r, t] <= big_m * model.Z[r, t]
        self.model.route_activation_constraint = Constraint(
            self.model.ROUTES, self.model.PERIODS, rule=route_activation_rule
        )
        
        # 9. Trip activation: if trips > 0, then Z = 1
        def trip_activation_rule(model, r, t):
            big_m = 1000000
            return model.T[r, t] <= big_m * model.Z[r, t]
        self.model.trip_activation_constraint = Constraint(
            self.model.ROUTES, self.model.PERIODS, rule=trip_activation_rule
        )
        
        logger.info("Constraints created")
    
    def solve(self, solver_name: str = "cbc", time_limit: int = 600, 
              mip_gap: float = 0.01) -> Dict[str, Any]:
        """
        Solve the optimization model.
        
        Returns:
            Dictionary with solver status, objective value, and solution data
        """
        try:
            logger.info(f"Solving Pyomo model with {solver_name}")
            
            if self.model is None:
                raise OptimizationError("Model not built. Call build_model() first.")
            
            # Create solver
            solver = SolverFactory(solver_name)
            
            # Set solver options
            if solver_name.lower() == "cbc":
                solver.options['seconds'] = time_limit
                solver.options['ratio'] = mip_gap
            elif solver_name.lower() == "highs":
                solver.options['time_limit'] = time_limit
                solver.options['mip_rel_gap'] = mip_gap
            elif solver_name.lower() == "gurobi":
                solver.options['TimeLimit'] = time_limit
                solver.options['MIPGap'] = mip_gap
            
            # Solve
            start_time = datetime.now()
            result = solver.solve(self.model, tee=False)
            solve_time = (datetime.now() - start_time).total_seconds()
            
            # Check solution status
            if result.solver.status == SolverStatus.ok and \
               result.solver.termination_condition == TerminationCondition.optimal:
                
                self.objective_value = value(self.model.objective)
                logger.info(f"Optimization completed: optimal solution found in {solve_time:.2f}s")
                logger.info(f"Total cost: ₹{self.objective_value:,.2f} (RAW RUPEES)")
                
                # Validate cost is realistic
                if self.objective_value < 2000000:  # Less than 20 lakhs
                    logger.warning(f"Total cost ₹{self.objective_value:,.2f} appears unrealistically low. "
                                 f"Possible scaling or missing-cost issue.")
                
                return {
                    "solver_status": "optimal",
                    "objective_value": float(self.objective_value),
                    "solve_time": solve_time,
                    "solver_name": solver_name
                }
            else:
                status_msg = f"{result.solver.status} / {result.solver.termination_condition}"
                logger.error(f"Optimization failed: {status_msg}")
                raise OptimizationError(f"Solver failed: {status_msg}")
                
        except Exception as e:
            logger.error(f"Error solving optimization model: {e}", exc_info=True)
            raise OptimizationError(f"Solver execution failed: {str(e)}")
    
    def extract_results(self) -> Dict[str, Any]:
        """Extract and format optimization results."""
        try:
            if self.model is None or self.objective_value is None:
                raise OptimizationError("No solution available")
            
            results = {
                "objective_value": float(self.objective_value),
                "solver_status": "optimal",
                "production_plan": self._extract_production_plan(),
                "shipment_plan": self._extract_shipment_plan(),
                "inventory_profile": self._extract_inventory_profile(),
                "trip_plan": self._extract_trip_plan(),
                "cost_breakdown": self._extract_cost_breakdown(),
                "utilization_metrics": self._extract_utilization_metrics(),
                "service_metrics": self._extract_service_metrics()
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error extracting optimization results: {e}", exc_info=True)
            raise OptimizationError(f"Result extraction failed: {str(e)}")
    
    def _extract_production_plan(self) -> List[Dict[str, Any]]:
        """Extract production plan from solution."""
        production_plan = []
        
        for p in self.model.PLANTS:
            for t in self.model.PERIODS:
                value = self.model.X[p, t].value
                if value and value > 0.001:
                    production_plan.append({
                        "plant_id": p,
                        "period": t,
                        "production_tonnes": round(float(value), 2)
                    })
        
        return production_plan
    
    def _extract_shipment_plan(self) -> List[Dict[str, Any]]:
        """Extract shipment plan from solution."""
        shipment_plan = []
        
        for r in self.model.ROUTES:
            for t in self.model.PERIODS:
                value = self.model.Y[r, t].value
                if value and value > 0.001:
                    shipment_plan.append({
                        "origin_plant_id": r[0],
                        "destination_node_id": r[1],
                        "period": t,
                        "transport_mode": r[2],
                        "shipment_tonnes": round(float(value), 2)
                    })
        
        return shipment_plan
    
    def _extract_inventory_profile(self) -> List[Dict[str, Any]]:
        """Extract inventory profile from solution."""
        inventory_profile = []
        
        for p in self.model.PLANTS:
            for t in self.model.PERIODS:
                value = self.model.I[p, t].value
                inventory_profile.append({
                    "plant_id": p,
                    "period": t,
                    "inventory_tonnes": round(float(value) if value else 0.0, 2)
                })
        
        return inventory_profile
    
    def _extract_trip_plan(self) -> List[Dict[str, Any]]:
        """Extract trip plan from solution."""
        trip_plan = []
        
        for r in self.model.ROUTES:
            for t in self.model.PERIODS:
                value = self.model.T[r, t].value
                if value and value > 0:
                    trip_plan.append({
                        "origin_plant_id": r[0],
                        "destination_node_id": r[1],
                        "period": t,
                        "transport_mode": r[2],
                        "trips": int(value)
                    })
        
        return trip_plan
    
    def _extract_cost_breakdown(self) -> Dict[str, float]:
        """Extract cost breakdown from solution (all in RAW RUPEES)."""
        cost_breakdown = {}
        
        # Production cost
        production_cost = sum(
            self.model.X[p, t].value * self.model.PROD_COST[p, t].value
            for p in self.model.PLANTS
            for t in self.model.PERIODS
            if self.model.X[p, t].value
        )
        cost_breakdown["production_cost"] = round(float(production_cost), 2)
        
        # Transport cost
        transport_cost = sum(
            self.model.Y[r, t].value * self.model.TRANSPORT_COST[r].value
            for r in self.model.ROUTES
            for t in self.model.PERIODS
            if self.model.Y[r, t].value
        )
        cost_breakdown["transport_cost"] = round(float(transport_cost), 2)
        
        # Fixed trip cost
        fixed_trip_cost = sum(
            self.model.T[r, t].value * self.model.FIXED_TRIP_COST[r].value
            for r in self.model.ROUTES
            for t in self.model.PERIODS
            if self.model.T[r, t].value
        )
        cost_breakdown["fixed_trip_cost"] = round(float(fixed_trip_cost), 2)
        
        # Holding cost
        holding_cost = sum(
            self.model.I[p, t].value * self.model.HOLDING_COST[p, t].value
            for p in self.model.PLANTS
            for t in self.model.PERIODS
            if self.model.I[p, t].value
        )
        cost_breakdown["holding_cost"] = round(float(holding_cost), 2)
        
        # Penalty cost
        penalty_cost = sum(
            self.model.U[c, t].value * self.model.PENALTY_COST.value
            for c in self.model.CUSTOMERS
            for t in self.model.PERIODS
            if self.model.U[c, t].value
        )
        cost_breakdown["penalty_cost"] = round(float(penalty_cost), 2)
        
        return cost_breakdown
    
    def _extract_utilization_metrics(self) -> Dict[str, Any]:
        """Extract utilization metrics."""
        # Calculate production utilization
        total_capacity = sum(
            self.model.PROD_CAPACITY[p, t].value
            for p in self.model.PLANTS
            for t in self.model.PERIODS
        )
        total_production = sum(
            self.model.X[p, t].value
            for p in self.model.PLANTS
            for t in self.model.PERIODS
            if self.model.X[p, t].value
        )
        production_util = (total_production / total_capacity) if total_capacity > 0 else 0.0
        
        # Calculate transport utilization
        total_trip_capacity = sum(
            self.model.T[r, t].value * self.model.VEHICLE_CAPACITY[r].value
            for r in self.model.ROUTES
            for t in self.model.PERIODS
            if self.model.T[r, t].value
        )
        total_shipment = sum(
            self.model.Y[r, t].value
            for r in self.model.ROUTES
            for t in self.model.PERIODS
            if self.model.Y[r, t].value
        )
        transport_util = (total_shipment / total_trip_capacity) if total_trip_capacity > 0 else 0.0
        
        return {
            "production_utilization": round(float(production_util), 4),
            "transport_utilization": round(float(transport_util), 4),
            "inventory_turns": 12.0  # Placeholder - calculate from actual data
        }
    
    def _extract_service_metrics(self) -> Dict[str, Any]:
        """Extract service level metrics."""
        total_demand = sum(
            self.model.DEMAND[c, t].value
            for c in self.model.CUSTOMERS
            for t in self.model.PERIODS
        )
        total_unmet = sum(
            self.model.U[c, t].value
            for c in self.model.CUSTOMERS
            for t in self.model.PERIODS
            if self.model.U[c, t].value
        )
        
        demand_fulfillment_rate = 1.0 - (total_unmet / total_demand) if total_demand > 0 else 1.0
        
        return {
            "demand_fulfillment_rate": round(float(demand_fulfillment_rate), 4),
            "stockout_events": sum(1 for c in self.model.CUSTOMERS for t in self.model.PERIODS
                                  if self.model.U[c, t].value and self.model.U[c, t].value > 0.001),
            "service_level": round(float(demand_fulfillment_rate), 4)
        }

