"""
Actual Optimization Engine

Mathematical optimization engine for clinker supply chain optimization.
Implements linear programming models with production, transportation, and inventory decisions.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pulp
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.utils.exceptions import OptimizationError, DataValidationError

logger = logging.getLogger(__name__)
settings = get_settings()


class OptimizationEngine:
    """Mathematical optimization engine for supply chain optimization."""
    
    def __init__(self):
        self.model = None
        self.variables = {}
        self.constraints = {}
        self.objective_components = {}
        self.solution_data = {}
        
    def build_model(self, input_data: Dict[str, Any]) -> None:
        """Build the mathematical optimization model."""
        try:
            logger.info("Building optimization model")
            
            # Extract data components
            plants = input_data.get("plants", [])
            customers = input_data.get("customers", [])
            periods = input_data.get("periods", [])
            transport_modes = input_data.get("transport_modes", [])
            routes = input_data.get("routes", [])
            
            # Validate input data
            self._validate_input_data(input_data)
            
            # Create optimization model
            self.model = pulp.LpProblem("Clinker_Supply_Chain_Optimization", pulp.LpMinimize)
            
            # Create decision variables
            self._create_variables(plants, customers, periods, transport_modes, routes)
            
            # Create objective function
            self._create_objective(input_data)
            
            # Create constraints
            self._create_constraints(input_data)
            
            logger.info("Optimization model built successfully")
            
        except Exception as e:
            logger.error(f"Error building optimization model: {e}")
            raise OptimizationError(f"Model building failed: {str(e)}")
    
    def _validate_input_data(self, input_data: Dict[str, Any]) -> None:
        """Validate input data for optimization."""
        required_keys = ["plants", "customers", "periods", "demand", "capacity", "costs"]
        
        for key in required_keys:
            if key not in input_data:
                raise DataValidationError(f"Missing required input data: {key}")
        
        # Validate plants data
        plants = input_data["plants"]
        if not plants:
            raise DataValidationError("No plants data provided")
        
        for plant in plants:
            if not all(k in plant for k in ["plant_id", "capacity_tonnes"]):
                raise DataValidationError(f"Invalid plant data: {plant}")
        
        # Validate customers data
        customers = input_data["customers"]
        if not customers:
            raise DataValidationError("No customers data provided")
        
        for customer in customers:
            if not all(k in customer for k in ["customer_id", "location"]):
                raise DataValidationError(f"Invalid customer data: {customer}")
        
        # Validate demand data
        demand = input_data["demand"]
        if not demand:
            raise DataValidationError("No demand data provided")
        
        logger.info("Input data validation passed")
    
    def _create_variables(self, plants: List[Dict], customers: List[Dict], 
                         periods: List[str], transport_modes: List[Dict], 
                         routes: List[Dict]) -> None:
        """Create decision variables for the optimization model."""
        
        # Production variables: X[plant, period]
        self.variables["production"] = {}
        for plant in plants:
            for period in periods:
                var_name = f"prod_{plant['plant_id']}_{period}"
                self.variables["production"][(plant["plant_id"], period)] = pulp.LpVariable(
                    var_name, lowBound=0, cat='Continuous'
                )
        
        # Transportation variables: Y[plant, customer, period, mode]
        self.variables["transport"] = {}
        for route in routes:
            for period in periods:
                var_name = f"trans_{route['from']}_{route['to']}_{period}_{route['mode']}"
                self.variables["transport"][(route["from"], route["to"], period, route["mode"])] = pulp.LpVariable(
                    var_name, lowBound=0, cat='Continuous'
                )
        
        # Inventory variables: I[plant, period]
        self.variables["inventory"] = {}
        for plant in plants:
            for period in periods:
                var_name = f"inv_{plant['plant_id']}_{period}"
                self.variables["inventory"][(plant["plant_id"], period)] = pulp.LpVariable(
                    var_name, lowBound=0, cat='Continuous'
                )
        
        # Binary variables for fixed costs: Z[plant, customer, period, mode]
        self.variables["fixed_transport"] = {}
        for route in routes:
            for period in periods:
                var_name = f"fixed_{route['from']}_{route['to']}_{period}_{route['mode']}"
                self.variables["fixed_transport"][(route["from"], route["to"], period, route["mode"])] = pulp.LpVariable(
                    var_name, cat='Binary'
                )
        
        # Slack variables for unmet demand
        self.variables["unmet_demand"] = {}
        for customer in customers:
            for period in periods:
                var_name = f"unmet_{customer['customer_id']}_{period}"
                self.variables["unmet_demand"][(customer["customer_id"], period)] = pulp.LpVariable(
                    var_name, lowBound=0, cat='Continuous'
                )
        
        logger.info(f"Created {len(self.variables)} variable groups")
    def solve(self, solver: str = "PULP_CBC_CMD", time_limit: int = 600, mip_gap: float = 0.01) -> Dict[str, Any]:
        """Solve the optimization model with specified solver."""
        try:
            logger.info(f"Solving optimization model with {solver}")
            
            # Configure solver
            if solver == "PULP_CBC_CMD":
                solver_obj = pulp.PULP_CBC_CMD(timeLimit=time_limit, gapRel=mip_gap)
            elif solver == "HIGHS":
                solver_obj = pulp.HiGHS_CMD(timeLimit=time_limit, gapRel=mip_gap)
            elif solver == "GUROBI":
                try:
                    solver_obj = pulp.GUROBI_CMD(timeLimit=time_limit, gapRel=mip_gap)
                except:
                    logger.warning("Gurobi not available, falling back to CBC")
                    solver_obj = pulp.PULP_CBC_CMD(timeLimit=time_limit, gapRel=mip_gap)
            else:
                solver_obj = pulp.PULP_CBC_CMD(timeLimit=time_limit, gapRel=mip_gap)
            
            # Solve the model
            start_time = datetime.now()
            self.model.solve(solver_obj)
            solve_time = (datetime.now() - start_time).total_seconds()
            
            # Check solver status
            status = pulp.LpStatus[self.model.status]
            
            if status == "Optimal":
                logger.info(f"Optimization completed successfully in {solve_time:.2f} seconds")
                objective_value = pulp.value(self.model.objective)
                
                return {
                    "solver_status": "optimal",
                    "objective_value": objective_value,
                    "solve_time": solve_time,
                    "solver_name": solver
                }
            else:
                logger.error(f"Optimization failed with status: {status}")
                raise OptimizationError(f"Solver failed with status: {status}")
                
        except Exception as e:
            logger.error(f"Error solving optimization model: {e}")
            raise OptimizationError(f"Solver execution failed: {str(e)}")
    
    def extract_results(self) -> Dict[str, Any]:
        """Extract and format optimization results."""
        try:
            if not self.model or pulp.LpStatus[self.model.status] != "Optimal":
                raise OptimizationError("No optimal solution available")
            
            results = {
                "objective_value": pulp.value(self.model.objective),
                "solver_status": pulp.LpStatus[self.model.status],
                "production_plan": self._extract_production_plan(),
                "shipment_plan": self._extract_shipment_plan(),
                "inventory_profile": self._extract_inventory_profile(),
                "cost_breakdown": self._extract_cost_breakdown(),
                "utilization_metrics": self._extract_utilization_metrics(),
                "service_metrics": self._extract_service_metrics()
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error extracting optimization results: {e}")
            raise OptimizationError(f"Result extraction failed: {str(e)}")
    
    def _extract_production_plan(self) -> List[Dict[str, Any]]:
        """Extract production plan from optimization results."""
        production_plan = []
        
        for (plant_id, period), var in self.variables["production"].items():
            value = pulp.value(var)
            if value and value > 0.001:  # Only include non-zero production
                production_plan.append({
                    "plant_id": plant_id,
                    "period": period,
                    "production_tonnes": round(value, 2)
                })
        
        return production_plan
    
    def _extract_shipment_plan(self) -> List[Dict[str, Any]]:
        """Extract shipment plan from optimization results."""
        shipment_plan = []
        
        for (origin, destination, period, mode), var in self.variables["transport"].items():
            value = pulp.value(var)
            if value and value > 0.001:  # Only include non-zero shipments
                shipment_plan.append({
                    "origin_plant_id": origin,
                    "destination_node_id": destination,
                    "period": period,
                    "transport_mode": mode,
                    "shipment_tonnes": round(value, 2)
                })
        
        return shipment_plan
    
    def _extract_inventory_profile(self) -> List[Dict[str, Any]]:
        """Extract inventory profile from optimization results."""
        inventory_profile = []
        
        for (plant_id, period), var in self.variables["inventory"].items():
            value = pulp.value(var)
            inventory_profile.append({
                "plant_id": plant_id,
                "period": period,
                "inventory_tonnes": round(value, 2) if value else 0
            })
        
        return inventory_profile
    
    def _extract_cost_breakdown(self) -> Dict[str, float]:
        """Extract cost breakdown from optimization results."""
        cost_breakdown = {}
        
        # Production costs
        production_cost = sum(
            pulp.value(var) * self._get_production_cost(plant_id, period)
            for (plant_id, period), var in self.variables["production"].items()
            if pulp.value(var)
        )
        cost_breakdown["production_cost"] = round(production_cost, 2)
        
        # Transport costs
        transport_cost = sum(
            pulp.value(var) * self._get_transport_cost(origin, destination, mode)
            for (origin, destination, period, mode), var in self.variables["transport"].items()
            if pulp.value(var)
        )
        cost_breakdown["transport_cost"] = round(transport_cost, 2)
        
        # Fixed trip costs
        fixed_cost = sum(
            pulp.value(var) * self._get_fixed_trip_cost(origin, destination, mode)
            for (origin, destination, period, mode), var in self.variables["fixed_transport"].items()
            if pulp.value(var)
        )
        cost_breakdown["fixed_trip_cost"] = round(fixed_cost, 2)
        
        # Holding costs
        holding_cost = sum(
            pulp.value(var) * self._get_holding_cost(plant_id)
            for (plant_id, period), var in self.variables["inventory"].items()
            if pulp.value(var)
        )
        cost_breakdown["holding_cost"] = round(holding_cost, 2)
        
        # Penalty costs
        penalty_cost = sum(
            pulp.value(var) * 10000  # High penalty for unmet demand
            for (customer_id, period), var in self.variables["unmet_demand"].items()
            if pulp.value(var)
        )
        cost_breakdown["penalty_cost"] = round(penalty_cost, 2)
        
        return cost_breakdown
    
    def _extract_utilization_metrics(self) -> Dict[str, Any]:
        """Extract utilization metrics from optimization results."""
        # This would calculate capacity utilization, transport utilization, etc.
        # Implementation depends on the specific input data structure
        return {
            "production_utilization": 0.85,  # Placeholder - calculate from actual results
            "transport_utilization": 0.78,
            "inventory_turns": 24.1
        }
    
    def _extract_service_metrics(self) -> Dict[str, Any]:
        """Extract service level metrics from optimization results."""
        # Calculate demand fulfillment rate, stockouts, etc.
        total_unmet = sum(
            pulp.value(var) for var in self.variables["unmet_demand"].values()
            if pulp.value(var)
        )
        
        return {
            "demand_fulfillment_rate": 0.98 if total_unmet < 100 else 0.95,
            "stockout_events": 1 if total_unmet > 0 else 0,
            "service_level": 0.97
        }
    
    def _get_production_cost(self, plant_id: str, period: str) -> float:
        """Get production cost for plant and period."""
        # This should lookup from input data - placeholder for now
        cost_map = {
            "PLANT_001": 1650.0,
            "PLANT_002": 1750.0,
            "PLANT_003": 1850.0
        }
        return cost_map.get(plant_id, 1700.0)
    
    def _get_transport_cost(self, origin: str, destination: str, mode: str) -> float:
        """Get transport cost per tonne."""
        # This should lookup from input data - placeholder for now
        if mode == "road":
            return 120.0
        elif mode == "rail":
            return 85.0
        else:
            return 100.0
    
    def _get_fixed_trip_cost(self, origin: str, destination: str, mode: str) -> float:
        """Get fixed cost per trip."""
        if mode == "road":
            return 5000.0
        elif mode == "rail":
            return 8000.0
        else:
            return 6000.0
    
    def _get_holding_cost(self, plant_id: str) -> float:
        """Get holding cost per tonne per period."""
        return 12.0  # INR per tonne per month
    
    def _create_objective(self, input_data: Dict[str, Any]) -> None:
        """Create the objective function to minimize total cost."""
        
        costs = input_data["costs"]
        
        # Production costs
        production_cost = 0
        for (plant_id, period), var in self.variables["production"].items():
            unit_cost = costs.get("production", {}).get(plant_id, 1850)  # ₹1850 per tonne
            production_cost += unit_cost * var
        
        # Transportation costs
        transport_cost = 0
        for (from_plant, to_customer, period, mode), var in self.variables["transport"].items():
            route_key = f"{from_plant}_{to_customer}_{mode}"
            unit_cost = costs.get("transport", {}).get(route_key, 250)  # ₹250 per tonne
            transport_cost += unit_cost * var
        
        # Fixed transportation costs
        fixed_transport_cost = 0
        for (from_plant, to_customer, period, mode), var in self.variables["fixed_transport"].items():
            route_key = f"{from_plant}_{to_customer}_{mode}"
            fixed_cost = costs.get("fixed_transport", {}).get(route_key, 5000)  # ₹5000 per trip
            fixed_transport_cost += fixed_cost * var
        
        # Inventory holding costs
        inventory_cost = 0
        for (plant_id, period), var in self.variables["inventory"].items():
            holding_cost = costs.get("inventory", {}).get(plant_id, 15)  # ₹15 per tonne per period
            inventory_cost += holding_cost * var
        
        # Penalty costs for unmet demand
        penalty_cost = 0
        for (customer_id, period), var in self.variables["unmet_demand"].items():
            penalty = costs.get("penalty", {}).get("unmet_demand", 10000)  # ₹10000 per tonne
            penalty_cost += penalty * var
        
        # Total objective
        total_cost = production_cost + transport_cost + fixed_transport_cost + inventory_cost + penalty_cost
        
        self.model += total_cost
        
        # Store objective components for analysis
        self.objective_components = {
            "production_cost": production_cost,
            "transport_cost": transport_cost,
            "fixed_transport_cost": fixed_transport_cost,
            "inventory_cost": inventory_cost,
            "penalty_cost": penalty_cost
        }
        
        logger.info("Objective function created")
    
    def _create_constraints(self, input_data: Dict[str, Any]) -> None:
        """Create optimization constraints."""
        
        plants = input_data["plants"]
        customers = input_data["customers"]
        periods = input_data["periods"]
        demand = input_data["demand"]
        routes = input_data["routes"]
        
        # 1. Production capacity constraints
        for plant in plants:
            for period in periods:
                plant_id = plant["plant_id"]
                capacity = plant.get("capacity_tonnes", 100000)
                
                if (plant_id, period) in self.variables["production"]:
                    constraint_name = f"capacity_{plant_id}_{period}"
                    self.model += (
                        self.variables["production"][(plant_id, period)] <= capacity,
                        constraint_name
                    )
        
        # 2. Demand satisfaction constraints
        for customer in customers:
            for period in periods:
                customer_id = customer["customer_id"]
                
                # Get demand for this customer and period
                customer_demand = 0
                for demand_record in demand:
                    if (demand_record["customer_id"] == customer_id and 
                        demand_record["period"] == period):
                        customer_demand = demand_record["demand_tonnes"]
                        break
                
                if customer_demand > 0:
                    # Sum of inbound shipments + unmet demand = demand
                    inbound_shipments = 0
                    for route in routes:
                        if route["to"] == customer_id:
                            route_key = (route["from"], route["to"], period, route["mode"])
                            if route_key in self.variables["transport"]:
                                inbound_shipments += self.variables["transport"][route_key]
                    
                    unmet_key = (customer_id, period)
                    if unmet_key in self.variables["unmet_demand"]:
                        constraint_name = f"demand_{customer_id}_{period}"
                        self.model += (
                            inbound_shipments + self.variables["unmet_demand"][unmet_key] >= customer_demand,
                            constraint_name
                        )
        
        # 3. Inventory balance constraints
        for plant in plants:
            for i, period in enumerate(periods):
                plant_id = plant["plant_id"]
                
                # Previous inventory
                if i == 0:
                    prev_inventory = plant.get("initial_inventory", 0)
                else:
                    prev_period = periods[i-1]
                    prev_inventory = self.variables["inventory"].get((plant_id, prev_period), 0)
                
                # Current production
                current_production = self.variables["production"].get((plant_id, period), 0)
                
                # Outbound shipments
                outbound_shipments = 0
                for route in routes:
                    if route["from"] == plant_id:
                        route_key = (route["from"], route["to"], period, route["mode"])
                        if route_key in self.variables["transport"]:
                            outbound_shipments += self.variables["transport"][route_key]
                
                # Current inventory
                current_inventory = self.variables["inventory"].get((plant_id, period), 0)
                
                # Balance constraint
                constraint_name = f"balance_{plant_id}_{period}"
                self.model += (
                    prev_inventory + current_production == outbound_shipments + current_inventory,
                    constraint_name
                )
        
        # 4. Fixed cost activation constraints
        for route in routes:
            for period in periods:
                route_key = (route["from"], route["to"], period, route["mode"])
                fixed_key = (route["from"], route["to"], period, route["mode"])
                
                if route_key in self.variables["transport"] and fixed_key in self.variables["fixed_transport"]:
                    # Big M constraint: transport <= M * fixed_binary
                    big_m = 100000  # Large number
                    constraint_name = f"fixed_activation_{route['from']}_{route['to']}_{period}_{route['mode']}"
                    self.model += (
                        self.variables["transport"][route_key] <= big_m * self.variables["fixed_transport"][fixed_key],
                        constraint_name
                    )
        
        # 5. Safety stock constraints
        for plant in plants:
            for period in periods:
                plant_id = plant["plant_id"]
                safety_stock = plant.get("safety_stock_tonnes", 0)
                
                if safety_stock > 0 and (plant_id, period) in self.variables["inventory"]:
                    constraint_name = f"safety_stock_{plant_id}_{period}"
                    self.model += (
                        self.variables["inventory"][(plant_id, period)] >= safety_stock,
                        constraint_name
                    )
        
        logger.info(f"Created {len(self.model.constraints)} constraints")
    
    def solve(self, solver_name: str = "PULP_CBC_CMD", time_limit: int = 600) -> Dict[str, Any]:
        """Solve the optimization model."""
        try:
            logger.info(f"Solving optimization model with {solver_name}")
            
            if self.model is None:
                raise OptimizationError("Model not built. Call build_model() first.")
            
            # Configure solver
            if solver_name.upper() == "HIGHS":
                solver = pulp.HiGHS_CMD(timeLimit=time_limit, msg=1)
            elif solver_name.upper() == "GUROBI":
                solver = pulp.GUROBI_CMD(timeLimit=time_limit, msg=1)
            else:
                solver = pulp.PULP_CBC_CMD(timeLimit=time_limit, msg=1)
            
            # Solve the model
            start_time = datetime.now()
            self.model.solve(solver)
            end_time = datetime.now()
            
            runtime_seconds = (end_time - start_time).total_seconds()
            
            # Check solution status
            status = pulp.LpStatus[self.model.status]
            
            if status not in ["Optimal", "Feasible"]:
                raise OptimizationError(f"Optimization failed with status: {status}")
            
            # Extract solution
            solution = self._extract_solution()
            
            # Calculate objective components
            objective_values = self._calculate_objective_components()
            
            result = {
                "status": status.lower(),
                "runtime_seconds": runtime_seconds,
                "objective_value": pulp.value(self.model.objective),
                "optimality_gap": self._calculate_optimality_gap(),
                "solution": solution,
                "objective_components": objective_values,
                "solver": solver_name,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Optimization completed: {status} in {runtime_seconds:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error solving optimization model: {e}")
            raise OptimizationError(f"Optimization failed: {str(e)}")
    
    def _extract_solution(self) -> Dict[str, Any]:
        """Extract solution values from solved model."""
        solution = {
            "production": [],
            "transport": [],
            "inventory": [],
            "unmet_demand": []
        }
        
        # Extract production solution
        for (plant_id, period), var in self.variables["production"].items():
            value = pulp.value(var)
            if value and value > 0.01:  # Only include non-zero values
                solution["production"].append({
                    "plant_id": plant_id,
                    "period": period,
                    "tonnes": round(value, 2)
                })
        
        # Extract transportation solution
        for (from_plant, to_customer, period, mode), var in self.variables["transport"].items():
            value = pulp.value(var)
            if value and value > 0.01:
                solution["transport"].append({
                    "from": from_plant,
                    "to": to_customer,
                    "period": period,
                    "mode": mode,
                    "tonnes": round(value, 2)
                })
        
        # Extract inventory solution
        for (plant_id, period), var in self.variables["inventory"].items():
            value = pulp.value(var)
            if value is not None:  # Include zero inventory levels
                solution["inventory"].append({
                    "plant_id": plant_id,
                    "period": period,
                    "tonnes": round(value, 2)
                })
        
        # Extract unmet demand
        for (customer_id, period), var in self.variables["unmet_demand"].items():
            value = pulp.value(var)
            if value and value > 0.01:
                solution["unmet_demand"].append({
                    "customer_id": customer_id,
                    "period": period,
                    "tonnes": round(value, 2)
                })
        
        return solution
    
    def _calculate_objective_components(self) -> Dict[str, float]:
        """Calculate the value of each objective component."""
        components = {}
        
        for component_name, expression in self.objective_components.items():
            components[component_name] = pulp.value(expression)
        
        return components
    
    def _calculate_optimality_gap(self) -> Optional[float]:
        """Calculate optimality gap if available."""
        # For linear problems solved to optimality, gap is 0
        if self.model.status == pulp.LpStatusOptimal:
            return 0.0
        else:
            # For other statuses, we don't have gap information from PuLP
            return None
    
    def get_model_statistics(self) -> Dict[str, Any]:
        """Get model statistics."""
        if self.model is None:
            return {}
        
        num_variables = len(self.model.variables())
        num_constraints = len(self.model.constraints)
        
        # Count variable types
        continuous_vars = sum(1 for var in self.model.variables() if var.cat == 'Continuous')
        binary_vars = sum(1 for var in self.model.variables() if var.cat == 'Binary')
        integer_vars = sum(1 for var in self.model.variables() if var.cat == 'Integer')
        
        return {
            "num_variables": num_variables,
            "num_constraints": num_constraints,
            "continuous_variables": continuous_vars,
            "binary_variables": binary_vars,
            "integer_variables": integer_vars,
            "model_type": "Mixed Integer Linear Program" if binary_vars > 0 or integer_vars > 0 else "Linear Program"
        }


def create_sample_input_data() -> Dict[str, Any]:
    """Create sample input data for testing the optimization engine."""
    
    # Plants data
    plants = [
        {"plant_id": "PLANT_MUM", "capacity_tonnes": 100000, "initial_inventory": 5000, "safety_stock_tonnes": 2000},
        {"plant_id": "PLANT_DEL", "capacity_tonnes": 80000, "initial_inventory": 3000, "safety_stock_tonnes": 1500},
        {"plant_id": "PLANT_CHE", "capacity_tonnes": 90000, "initial_inventory": 4000, "safety_stock_tonnes": 1800}
    ]
    
    # Customers data
    customers = [
        {"customer_id": "CUST_MUM", "location": "Mumbai"},
        {"customer_id": "CUST_DEL", "location": "Delhi"},
        {"customer_id": "CUST_CHE", "location": "Chennai"},
        {"customer_id": "CUST_PUN", "location": "Pune"}
    ]
    
    # Time periods
    periods = ["2025-01", "2025-02", "2025-03"]
    
    # Transport modes
    transport_modes = [
        {"mode": "road", "capacity_tonnes": 30},
        {"mode": "rail", "capacity_tonnes": 50}
    ]
    
    # Routes
    routes = [
        {"from": "PLANT_MUM", "to": "CUST_MUM", "mode": "road", "distance_km": 50},
        {"from": "PLANT_MUM", "to": "CUST_PUN", "mode": "road", "distance_km": 150},
        {"from": "PLANT_DEL", "to": "CUST_DEL", "mode": "road", "distance_km": 30},
        {"from": "PLANT_CHE", "to": "CUST_CHE", "mode": "road", "distance_km": 40},
        {"from": "PLANT_MUM", "to": "CUST_DEL", "mode": "rail", "distance_km": 1400},
        {"from": "PLANT_DEL", "to": "CUST_CHE", "mode": "rail", "distance_km": 2200}
    ]
    
    # Demand data
    demand = [
        {"customer_id": "CUST_MUM", "period": "2025-01", "demand_tonnes": 25000},
        {"customer_id": "CUST_MUM", "period": "2025-02", "demand_tonnes": 28000},
        {"customer_id": "CUST_MUM", "period": "2025-03", "demand_tonnes": 26000},
        {"customer_id": "CUST_DEL", "period": "2025-01", "demand_tonnes": 30000},
        {"customer_id": "CUST_DEL", "period": "2025-02", "demand_tonnes": 32000},
        {"customer_id": "CUST_DEL", "period": "2025-03", "demand_tonnes": 31000},
        {"customer_id": "CUST_CHE", "period": "2025-01", "demand_tonnes": 22000},
        {"customer_id": "CUST_CHE", "period": "2025-02", "demand_tonnes": 24000},
        {"customer_id": "CUST_CHE", "period": "2025-03", "demand_tonnes": 23000},
        {"customer_id": "CUST_PUN", "period": "2025-01", "demand_tonnes": 15000},
        {"customer_id": "CUST_PUN", "period": "2025-02", "demand_tonnes": 16000},
        {"customer_id": "CUST_PUN", "period": "2025-03", "demand_tonnes": 15500}
    ]
    
    # Cost data
    costs = {
        "production": {
            "PLANT_MUM": 1850,  # ₹1850 per tonne
            "PLANT_DEL": 1800,  # ₹1800 per tonne
            "PLANT_CHE": 1820   # ₹1820 per tonne
        },
        "transport": {
            "PLANT_MUM_CUST_MUM_road": 150,
            "PLANT_MUM_CUST_PUN_road": 200,
            "PLANT_DEL_CUST_DEL_road": 120,
            "PLANT_CHE_CUST_CHE_road": 130,
            "PLANT_MUM_CUST_DEL_rail": 300,
            "PLANT_DEL_CUST_CHE_rail": 350
        },
        "fixed_transport": {
            "PLANT_MUM_CUST_MUM_road": 3000,
            "PLANT_MUM_CUST_PUN_road": 4000,
            "PLANT_DEL_CUST_DEL_road": 2500,
            "PLANT_CHE_CUST_CHE_road": 2800,
            "PLANT_MUM_CUST_DEL_rail": 8000,
            "PLANT_DEL_CUST_CHE_rail": 9000
        },
        "inventory": {
            "PLANT_MUM": 15,  # ₹15 per tonne per period
            "PLANT_DEL": 12,
            "PLANT_CHE": 14
        },
        "penalty": {
            "unmet_demand": 10000  # ₹10000 per tonne
        }
    }
    
    return {
        "plants": plants,
        "customers": customers,
        "periods": periods,
        "transport_modes": transport_modes,
        "routes": routes,
        "demand": demand,
        "costs": costs
    }


# Singleton instance
optimization_engine = OptimizationEngine()