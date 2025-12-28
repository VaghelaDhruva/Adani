"""
Multi-mode transport optimization validator and fine-tuner.
Validates SBQ logic, integer trip feasibility, and capacity consistency.
"""

from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
from pyomo.environ import value

from app.utils.exceptions import OptimizationError


class TransportValidator:
    """
    Validates and fine-tunes multi-mode transport optimization results.
    Ensures SBQ feasibility, integer trip consistency, and cost accuracy.
    """
    
    def __init__(self, model_data: Dict[str, Any], solution: Dict[str, Any]):
        """
        Initialize with model data and solution.
        
        Args:
            model_data: Original model input data
            solution: Optimization solution results
        """
        self.model_data = model_data
        self.solution = solution
        self.routes_df = model_data["transport_routes_modes"]
        self.validation_results = {}
    
    def validate_solution(self) -> Dict[str, Any]:
        """
        Perform comprehensive validation of transport solution.
        
        Returns:
            Dict with validation results and any issues found
        """
        validation_results = {
            "sbq_feasibility": self._validate_sbq_feasibility(),
            "integer_trip_consistency": self._validate_integer_trips(),
            "capacity_constraints": self._validate_capacity_constraints(),
            "cost_consistency": self._validate_cost_consistency(),
            "infeasible_routes": self._detect_infeasible_routes(),
            "overall_status": "passed"
        }
        
        # Check overall status
        failed_validations = [
            name for name, result in validation_results.items()
            if name != "overall_status" and not result.get("passed", True)
        ]
        
        if failed_validations:
            validation_results["overall_status"] = "failed"
            validation_results["failed_validations"] = failed_validations
        
        self.validation_results = validation_results
        return validation_results
    
    def _validate_sbq_feasibility(self) -> Dict[str, Any]:
        """
        Validate SBQ (minimum batch quantity) constraints are satisfied.
        """
        issues = []
        passed = True
        
        # Get shipments and trips from solution
        shipments = self.solution.get("shipments", [])
        trips = self.solution.get("trips", [])
        
        # Create lookup dictionaries
        shipment_lookup = {}
        for shipment in shipments:
            key = (shipment["origin"], shipment["destination"], shipment["mode"], shipment["period"])
            shipment_lookup[key] = shipment["tonnes"]
        
        trips_lookup = {}
        for trip in trips:
            key = (trip["origin"], trip["destination"], trip["mode"], trip["period"])
            trips_lookup[key] = trip["trips"]
        
        # Validate SBQ for each route with positive shipments
        for _, route in self.routes_df.iterrows():
            origin = route["origin_plant_id"]
            dest = route["destination_node_id"]
            mode = route["transport_mode"]
            sbq = route.get("min_batch_quantity_tonnes", 0)
            vehicle_cap = route.get("vehicle_capacity_tonnes", 0)
            
            if sbq <= 0:
                continue  # No SBQ constraint for this route
            
            # Check all periods for this route
            for period in self._get_periods():
                key = (origin, dest, mode, period)
                
                if key in shipment_lookup:
                    shipment_qty = shipment_lookup[key]
                    trip_count = trips_lookup.get(key, 0)
                    
                    # SBQ validation: shipment >= SBQ if trips > 0
                    if trip_count > 0 and shipment_qty < sbq - 1e-6:  # Small tolerance
                        issues.append({
                            "route": f"{origin}->{dest} ({mode})",
                            "period": period,
                            "issue": f"Shipment {shipment_qty:.2f} < SBQ {sbq:.2f}",
                            "trips": trip_count
                        })
                        passed = False
                    
                    # Capacity validation: shipment <= trips * vehicle_capacity
                    if trip_count > 0 and vehicle_cap > 0:
                        max_shipment = trip_count * vehicle_cap
                        if shipment_qty > max_shipment + 1e-6:
                            issues.append({
                                "route": f"{origin}->{dest} ({mode})",
                                "period": period,
                                "issue": f"Shipment {shipment_qty:.2f} > capacity {max_shipment:.2f}",
                                "trips": trip_count,
                                "vehicle_capacity": vehicle_cap
                            })
                            passed = False
        
        return {
            "passed": passed,
            "issues": issues,
            "total_issues": len(issues)
        }
    
    def _validate_integer_trips(self) -> Dict[str, Any]:
        """
        Validate that trips are properly integer and feasible.
        """
        issues = []
        passed = True
        
        trips = self.solution.get("trips", [])
        
        for trip in trips:
            origin = trip["origin"]
            dest = trip["destination"]
            mode = trip["mode"]
            period = trip["period"]
            trip_count = trip["trips"]
            
            # Check integer property
            if not isinstance(trip_count, int) and abs(trip_count - round(trip_count)) > 1e-6:
                issues.append({
                    "route": f"{origin}->{dest} ({mode})",
                    "period": period,
                    "issue": f"Non-integer trip count: {trip_count}",
                    "value": trip_count
                })
                passed = False
            
            # Check non-negative
            if trip_count < 0:
                issues.append({
                    "route": f"{origin}->{dest} ({mode})",
                    "period": period,
                    "issue": f"Negative trip count: {trip_count}",
                    "value": trip_count
                })
                passed = False
        
        return {
            "passed": passed,
            "issues": issues,
            "total_issues": len(issues)
        }
    
    def _validate_capacity_constraints(self) -> Dict[str, Any]:
        """
        Validate capacity constraints are respected.
        """
        issues = []
        passed = True
        
        # Get production data
        production = self.solution.get("production", [])
        prod_lookup = {f"{p['plant']}_{p['period']}": p["tonnes"] for p in production}
        
        # Get capacity data
        capacity_df = self.model_data["production_capacity_cost"]
        
        for _, cap_row in capacity_df.iterrows():
            plant = cap_row["plant_id"]
            period = cap_row["period"]
            max_capacity = cap_row.get("max_capacity_tonnes", 0)
            
            key = f"{plant}_{period}"
            actual_prod = prod_lookup.get(key, 0)
            
            if actual_prod > max_capacity + 1e-6:
                issues.append({
                    "plant": plant,
                    "period": period,
                    "issue": f"Production {actual_prod:.2f} > capacity {max_capacity:.2f}",
                    "actual": actual_prod,
                    "capacity": max_capacity
                })
                passed = False
        
        return {
            "passed": passed,
            "issues": issues,
            "total_issues": len(issues)
        }
    
    def _validate_cost_consistency(self) -> Dict[str, Any]:
        """
        Validate cost calculations are consistent with solution.
        """
        issues = []
        passed = True
        
        # Extract solution costs
        solution_costs = self.solution.get("costs", {})
        
        # Recalculate costs from solution
        recalculated_costs = self._recalculate_costs()
        
        # Compare costs (allow small tolerance)
        tolerance = 1e-3
        for cost_type in ["production_cost", "transport_cost", "fixed_trip_cost", "holding_cost"]:
            solution_value = solution_costs.get(cost_type, 0)
            recalculated_value = recalculated_costs.get(cost_type, 0)
            
            if abs(solution_value - recalculated_value) > tolerance:
                issues.append({
                    "cost_type": cost_type,
                    "solution_value": solution_value,
                    "recalculated_value": recalculated_value,
                    "difference": abs(solution_value - recalculated_value)
                })
                passed = False
        
        return {
            "passed": passed,
            "issues": issues,
            "total_issues": len(issues),
            "solution_costs": solution_costs,
            "recalculated_costs": recalculated_costs
        }
    
    def _detect_infeasible_routes(self) -> Dict[str, Any]:
        """
        Detect routes with infeasible SBQ or capacity settings.
        """
        infeasible_routes = []
        
        for _, route in self.routes_df.iterrows():
            origin = route["origin_plant_id"]
            dest = route["destination_node_id"]
            mode = route["transport_mode"]
            sbq = route.get("min_batch_quantity_tonnes", 0)
            vehicle_cap = route.get("vehicle_capacity_tonnes", 0)
            
            issues = []
            
            # Check SBQ > vehicle capacity (infeasible)
            if sbq > 0 and vehicle_cap > 0 and sbq > vehicle_cap:
                issues.append(f"SBQ {sbq} > vehicle capacity {vehicle_cap}")
            
            # Check zero capacity with positive SBQ
            if sbq > 0 and vehicle_cap <= 0:
                issues.append(f"Positive SBQ {sbq} but zero/negative vehicle capacity")
            
            # Check negative values
            if sbq < 0:
                issues.append(f"Negative SBQ: {sbq}")
            if vehicle_cap < 0:
                issues.append(f"Negative vehicle capacity: {vehicle_cap}")
            
            if issues:
                infeasible_routes.append({
                    "route": f"{origin}->{dest} ({mode})",
                    "issues": issues,
                    "sbq": sbq,
                    "vehicle_capacity": vehicle_cap
                })
        
        return {
            "infeasible_routes": infeasible_routes,
            "total_infeasible": len(infeasible_routes)
        }
    
    def _recalculate_costs(self) -> Dict[str, float]:
        """
        Recalculate costs from solution variables.
        """
        costs = {
            "production_cost": 0.0,
            "transport_cost": 0.0,
            "fixed_trip_cost": 0.0,
            "holding_cost": 0.0
        }
        
        # Production costs
        production = self.solution.get("production", [])
        prod_cost_df = self.model_data["production_capacity_cost"]
        prod_cost_lookup = {
            f"{row['plant_id']}_{row['period']}": row.get("variable_cost_per_tonne", 0)
            for _, row in prod_cost_df.iterrows()
        }
        
        for prod in production:
            key = f"{prod['plant']}_{prod['period']}"
            cost_per_tonne = prod_cost_lookup.get(key, 0)
            costs["production_cost"] += prod["tonnes"] * cost_per_tonne
        
        # Transport costs
        shipments = self.solution.get("shipments", [])
        trips = self.solution.get("trips", [])
        
        # Create lookup for route costs
        route_costs = {}
        for _, route in self.routes_df.iterrows():
            key = (route["origin_plant_id"], route["destination_node_id"], route["transport_mode"])
            route_costs[key] = {
                "cost_per_tonne": route.get("cost_per_tonne", 0),
                "fixed_cost_per_trip": route.get("fixed_cost_per_trip", 0)
            }
        
        # Variable transport costs
        for shipment in shipments:
            key = (shipment["origin"], shipment["destination"], shipment["mode"])
            cost_per_tonne = route_costs.get(key, {}).get("cost_per_tonne", 0)
            costs["transport_cost"] += shipment["tonnes"] * cost_per_tonne
        
        # Fixed trip costs
        for trip in trips:
            key = (trip["origin"], trip["destination"], trip["mode"])
            fixed_cost_per_trip = route_costs.get(key, {}).get("fixed_cost_per_trip", 0)
            costs["fixed_trip_cost"] += trip["trips"] * fixed_cost_per_trip
        
        # Holding costs (simplified - would need inventory data)
        # This is a placeholder implementation
        costs["holding_cost"] = 0.0
        
        return costs
    
    def _get_periods(self) -> List[Any]:
        """Get list of periods from model data."""
        if "time_periods" in self.model_data:
            return list(self.model_data["time_periods"])
        
        # Extract from demand forecast
        demand_df = self.model_data.get("demand_forecast", pd.DataFrame())
        if "period" in demand_df.columns:
            return sorted(demand_df["period"].unique())
        
        return []
    
    def suggest_fixes(self) -> List[Dict[str, Any]]:
        """
        Suggest fixes for identified validation issues.
        """
        fixes = []
        
        if not self.validation_results:
            self.validate_solution()
        
        # SBQ fixes
        sbq_result = self.validation_results.get("sbq_feasibility", {})
        if not sbq_result.get("passed", True):
            for issue in sbq_result.get("issues", []):
                fixes.append({
                    "type": "sbq_adjustment",
                    "issue": issue["issue"],
                    "suggestion": "Reduce SBQ or increase vehicle capacity",
                    "route": issue["route"],
                    "period": issue["period"]
                })
        
        # Infeasible route fixes
        infeasible_result = self.validation_results.get("infeasible_routes", {})
        for route_info in infeasible_result.get("infeasible_routes", []):
            for issue in route_info["issues"]:
                if "SBQ > vehicle capacity" in issue:
                    fixes.append({
                        "type": "route_parameter_fix",
                        "issue": issue,
                        "suggestion": f"Reduce SBQ to <= {route_info['vehicle_capacity']} or increase vehicle capacity",
                        "route": route_info["route"]
                    })
        
        return fixes
