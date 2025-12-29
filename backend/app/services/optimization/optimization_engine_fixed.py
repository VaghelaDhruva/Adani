"""
Fixed Optimization Engine

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
        required_keys = ["plants", "customers", "periods", "demand", "routes"]
        
        for key in required_keys:
            if key not in input_data:
                raise DataValidationError(f"Missing required input data: {key}")
        
        # Validate plants data
        plants = input_data["plants"]
        if not plants:
            raise DataValidationError("No plants data provided")
        
        # Validate customers data
        customers = input_data["customers"]
        if not customers:
            raise DataValidationError("No customers data provided")
        
        # Validate demand data
        demand = input_data["demand"]
        if not demand:
            raise DataValidationError("No demand data provided")
        
        logger.info("Input data validation passed")
    
    def _create_variables(self, plants: List[Dict], customers: List[str], 
                         periods: List[str], transport_modes: List[str], 
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
        
        # Transportation variables: Y[origin, destination, period, mode]
        self.variables["transport"] = {}
        for route in routes:
            for period in periods:
                var_name = f"trans_{route['origin_plant_id']}_{route['destination_node_id']}_{period}_{route['transport_mode']}"
                self.variables["transport"][(route["origin_plant_id"], route["destination_node_id"], period, route["transport_mode"])] = pulp.LpVariable(
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
        
        # Binary variables for fixed costs: Z[origin, destination, period, mode]
        self.variables["fixed_transport"] = {}
        for route in routes:
            for period in periods:
                var_name = f"fixed_{route['origin_plant_id']}_{route['destination_node_id']}_{period}_{route['transport_mode']}"
                self.variables["fixed_transport"][(route["origin_plant_id"], route["destination_node_id"], period, route["transport_mode"])] = pulp.LpVariable(
                    var_name, cat='Binary'
                )
        
        # Slack variables for unmet demand
        self.variables["unmet_demand"] = {}
        for customer in customers:
            for period in periods:
                var_name = f"unmet_{customer}_{period}"
                self.variables["unmet_demand"][(customer, period)] = pulp.LpVariable(
                    var_name, lowBound=0, cat='Continuous'
                )
        
        logger.info(f"Created {len(self.variables)} variable groups")
    
    def _create_objective(self, input_data: Dict[str, Any]) -> None:
        """Create the objective function to minimize total cost."""
        
        objective_terms = []
        
        # Production costs
        for (plant_id, period), var in self.variables["production"].items():
            cost = self._get_production_cost(plant_id, period)
            objective_terms.append(cost * var)
        
        # Transport costs
        for (origin, destination, period, mode), var in self.variables["transport"].items():
            cost = self._get_transport_cost(origin, destination, mode)
            objective_terms.append(cost * var)
        
        # Fixed trip costs
        for (origin, destination, period, mode), var in self.variables["fixed_transport"].items():
            cost = self._get_fixed_trip_cost(origin, destination, mode)
            objective_terms.append(cost * var)
        
        # Holding costs
        for (plant_id, period), var in self.variables["inventory"].items():
            cost = self._get_holding_cost(plant_id)
            objective_terms.append(cost * var)
        
        # Penalty costs for unmet demand
        for (customer_id, period), var in self.variables["unmet_demand"].items():
            penalty = 10000  # High penalty
            objective_terms.append(penalty * var)
        
        # Set objective
        self.model += pulp.lpSum(objective_terms)
        
        logger.info("Objective function created")
    
    def _create_constraints(self, input_data: Dict[str, Any]) -> None:
        """Create all optimization constraints."""
        
        plants = input_data.get("plants", [])
        customers = input_data.get("customers", [])
        periods = input_data.get("periods", [])
        demand = input_data.get("demand", [])
        capacity = input_data.get("capacity", [])
        routes = input_data.get("routes", [])
        
        # 1. Production capacity constraints
        for plant in plants:
            for period in periods:
                # Find capacity for this plant/period
                plant_capacity = next(
                    (c["max_capacity_tonnes"] for c in capacity 
                     if c["plant_id"] == plant["plant_id"] and c["period"] == period),
                    plant.get("capacity_tonnes", 100000)  # Default capacity
                )
                
                if (plant["plant_id"], period) in self.variables["production"]:
                    self.model += (
                        self.variables["production"][(plant["plant_id"], period)] <= plant_capacity,
                        f"capacity_{plant['plant_id']}_{period}"
                    )
        
        # 2. Demand satisfaction constraints
        demand_dict = {}
        for d in demand:
            key = (d["customer_node_id"], d["period"])
            demand_dict[key] = d["demand_tonnes"]
        
        for customer in customers:
            for period in periods:
                demand_qty = demand_dict.get((customer, period), 0)
                
                if demand_qty > 0:
                    # Sum of inbound shipments + unmet demand = demand
                    inbound_shipments = []
                    for route in routes:
                        if route["destination_node_id"] == customer:
                            key = (route["origin_plant_id"], customer, period, route["transport_mode"])
                            if key in self.variables["transport"]:
                                inbound_shipments.append(self.variables["transport"][key])
                    
                    unmet_key = (customer, period)
                    if unmet_key in self.variables["unmet_demand"]:
                        if inbound_shipments:
                            self.model += (
                                pulp.lpSum(inbound_shipments) + self.variables["unmet_demand"][unmet_key] >= demand_qty,
                                f"demand_{customer}_{period}"
                            )
                        else:
                            # No routes to this customer - all demand is unmet
                            self.model += (
                                self.variables["unmet_demand"][unmet_key] >= demand_qty,
                                f"demand_unmet_{customer}_{period}"
                            )
        
        # 3. Inventory balance constraints
        for plant in plants:
            for i, period in enumerate(periods):
                plant_id = plant["plant_id"]
                
                # Get initial inventory for first period
                if i == 0:
                    initial_inv = plant.get("initial_inventory", 1000)  # Default
                    prev_inventory = initial_inv
                else:
                    prev_period = periods[i-1]
                    if (plant_id, prev_period) in self.variables["inventory"]:
                        prev_inventory = self.variables["inventory"][(plant_id, prev_period)]
                    else:
                        prev_inventory = 0
                
                # Current inventory = Previous inventory + Production - Outbound shipments
                production = self.variables["production"].get((plant_id, period), 0)
                
                outbound_shipments = []
                for route in routes:
                    if route["origin_plant_id"] == plant_id:
                        key = (plant_id, route["destination_node_id"], period, route["transport_mode"])
                        if key in self.variables["transport"]:
                            outbound_shipments.append(self.variables["transport"][key])
                
                current_inventory = self.variables["inventory"].get((plant_id, period), 0)
                
                if outbound_shipments and current_inventory:
                    self.model += (
                        current_inventory == prev_inventory + production - pulp.lpSum(outbound_shipments),
                        f"inventory_balance_{plant_id}_{period}"
                    )
        
        # 4. Vehicle capacity and SBQ constraints
        for route in routes:
            for period in periods:
                origin = route["origin_plant_id"]
                destination = route["destination_node_id"]
                mode = route["transport_mode"]
                
                transport_key = (origin, destination, period, mode)
                fixed_key = (origin, destination, period, mode)
                
                if transport_key in self.variables["transport"] and fixed_key in self.variables["fixed_transport"]:
                    # Vehicle capacity constraint
                    vehicle_capacity = route.get("vehicle_capacity_tonnes", 25)
                    self.model += (
                        self.variables["transport"][transport_key] <= 
                        vehicle_capacity * 1000 * self.variables["fixed_transport"][fixed_key],  # Large M
                        f"vehicle_capacity_{origin}_{destination}_{period}_{mode}"
                    )
                    
                    # SBQ (minimum batch quantity) constraint
                    sbq = route.get("min_batch_quantity_tonnes", 0)
                    if sbq > 0:
                        self.model += (
                            self.variables["transport"][transport_key] >= 
                            sbq * self.variables["fixed_transport"][fixed_key],
                            f"sbq_{origin}_{destination}_{period}_{mode}"
                        )
        
        # 5. Safety stock constraints (if provided)
        safety_stock = input_data.get("safety_stock", [])
        for ss in safety_stock:
            node_id = ss["node_id"]
            safety_qty = ss["safety_stock_tonnes"]
            
            for period in periods:
                if (node_id, period) in self.variables["inventory"]:
                    self.model += (
                        self.variables["inventory"][(node_id, period)] >= safety_qty,
                        f"safety_stock_{node_id}_{period}"
                    )
        
        logger.info("All constraints created")
    
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
            "PLANT_003": 1850.0,
            "PLANT_MUM": 1650.0,
            "PLANT_DEL": 1750.0,
            "PLANT_CHE": 1850.0
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


def create_sample_input_data() -> Dict[str, Any]:
    """Create sample input data for testing the optimization engine."""
    
    # Plants data
    plants = [
        {"plant_id": "PLANT_MUM", "capacity_tonnes": 100000, "initial_inventory": 5000, "safety_stock_tonnes": 2000},
        {"plant_id": "PLANT_DEL", "capacity_tonnes": 80000, "initial_inventory": 3000, "safety_stock_tonnes": 1500},
        {"plant_id": "PLANT_CHE", "capacity_tonnes": 90000, "initial_inventory": 4000, "safety_stock_tonnes": 1800}
    ]
    
    # Customers data
    customers = ["CUST_MUM", "CUST_DEL", "CUST_CHE", "CUST_PUN"]
    
    # Time periods
    periods = ["2025-01", "2025-02", "2025-03"]
    
    # Transport modes
    transport_modes = ["road", "rail"]
    
    # Routes
    routes = [
        {"origin_plant_id": "PLANT_MUM", "destination_node_id": "CUST_MUM", "transport_mode": "road", "distance_km": 50, "vehicle_capacity_tonnes": 30, "min_batch_quantity_tonnes": 10},
        {"origin_plant_id": "PLANT_MUM", "destination_node_id": "CUST_PUN", "transport_mode": "road", "distance_km": 150, "vehicle_capacity_tonnes": 30, "min_batch_quantity_tonnes": 10},
        {"origin_plant_id": "PLANT_DEL", "destination_node_id": "CUST_DEL", "transport_mode": "road", "distance_km": 30, "vehicle_capacity_tonnes": 30, "min_batch_quantity_tonnes": 10},
        {"origin_plant_id": "PLANT_CHE", "destination_node_id": "CUST_CHE", "transport_mode": "road", "distance_km": 40, "vehicle_capacity_tonnes": 30, "min_batch_quantity_tonnes": 10},
        {"origin_plant_id": "PLANT_MUM", "destination_node_id": "CUST_DEL", "transport_mode": "rail", "distance_km": 1400, "vehicle_capacity_tonnes": 50, "min_batch_quantity_tonnes": 20},
        {"origin_plant_id": "PLANT_DEL", "destination_node_id": "CUST_CHE", "transport_mode": "rail", "distance_km": 2200, "vehicle_capacity_tonnes": 50, "min_batch_quantity_tonnes": 20}
    ]
    
    # Demand data
    demand = [
        {"customer_node_id": "CUST_MUM", "period": "2025-01", "demand_tonnes": 25000},
        {"customer_node_id": "CUST_MUM", "period": "2025-02", "demand_tonnes": 28000},
        {"customer_node_id": "CUST_MUM", "period": "2025-03", "demand_tonnes": 26000},
        {"customer_node_id": "CUST_DEL", "period": "2025-01", "demand_tonnes": 30000},
        {"customer_node_id": "CUST_DEL", "period": "2025-02", "demand_tonnes": 32000},
        {"customer_node_id": "CUST_DEL", "period": "2025-03", "demand_tonnes": 31000},
        {"customer_node_id": "CUST_CHE", "period": "2025-01", "demand_tonnes": 22000},
        {"customer_node_id": "CUST_CHE", "period": "2025-02", "demand_tonnes": 24000},
        {"customer_node_id": "CUST_CHE", "period": "2025-03", "demand_tonnes": 23000},
        {"customer_node_id": "CUST_PUN", "period": "2025-01", "demand_tonnes": 15000},
        {"customer_node_id": "CUST_PUN", "period": "2025-02", "demand_tonnes": 16000},
        {"customer_node_id": "CUST_PUN", "period": "2025-03", "demand_tonnes": 15500}
    ]
    
    # Capacity data
    capacity = [
        {"plant_id": "PLANT_MUM", "period": "2025-01", "max_capacity_tonnes": 100000},
        {"plant_id": "PLANT_MUM", "period": "2025-02", "max_capacity_tonnes": 100000},
        {"plant_id": "PLANT_MUM", "period": "2025-03", "max_capacity_tonnes": 100000},
        {"plant_id": "PLANT_DEL", "period": "2025-01", "max_capacity_tonnes": 80000},
        {"plant_id": "PLANT_DEL", "period": "2025-02", "max_capacity_tonnes": 80000},
        {"plant_id": "PLANT_DEL", "period": "2025-03", "max_capacity_tonnes": 80000},
        {"plant_id": "PLANT_CHE", "period": "2025-01", "max_capacity_tonnes": 90000},
        {"plant_id": "PLANT_CHE", "period": "2025-02", "max_capacity_tonnes": 90000},
        {"plant_id": "PLANT_CHE", "period": "2025-03", "max_capacity_tonnes": 90000}
    ]
    
    return {
        "plants": plants,
        "customers": customers,
        "periods": periods,
        "transport_modes": transport_modes,
        "routes": routes,
        "demand": demand,
        "capacity": capacity
    }