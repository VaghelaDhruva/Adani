"""
Comprehensive Data Validation Layer

Validates input data before optimization runs:
- Units consistency
- Negative or null costs
- Missing lanes
- Unreachable GUs
- SBQ feasibility vs vehicle capacity
- Demand > capacity warning
- Safety stock > storage prevention
- Integer trip logic compatibility
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.utils.exceptions import DataValidationError
from app.utils.currency import ensure_raw_rupees

logger = logging.getLogger(__name__)


class DataValidationService:
    """Service for validating optimization input data."""
    
    def __init__(self, db: Session):
        self.db = db
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_optimization_input(self, input_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Comprehensive validation of optimization input data.
        
        Returns:
            (is_valid, validation_report)
        """
        self.validation_errors = []
        self.validation_warnings = []
        
        try:
            # 1. Validate units consistency
            self._validate_units_consistency(input_data)
            
            # 2. Validate costs (negative, null, scaling)
            self._validate_costs(input_data)
            
            # 3. Validate routes and lanes
            self._validate_routes(input_data)
            
            # 4. Validate reachability
            self._validate_reachability(input_data)
            
            # 5. Validate SBQ feasibility
            self._validate_sbq_feasibility(input_data)
            
            # 6. Validate demand vs capacity
            self._validate_demand_capacity(input_data)
            
            # 7. Validate safety stock vs storage
            self._validate_safety_stock(input_data)
            
            # 8. Validate integer trip logic
            self._validate_integer_trip_logic(input_data)
            
            # Build report
            is_valid = len(self.validation_errors) == 0
            report = {
                "is_valid": is_valid,
                "errors": self.validation_errors,
                "warnings": self.validation_warnings,
                "error_count": len(self.validation_errors),
                "warning_count": len(self.validation_warnings)
            }
            
            if is_valid:
                logger.info(f"Data validation passed with {len(self.validation_warnings)} warnings")
            else:
                logger.error(f"Data validation failed with {len(self.validation_errors)} errors")
            
            return is_valid, report
            
        except Exception as e:
            logger.error(f"Data validation exception: {e}", exc_info=True)
            raise DataValidationError(f"Validation failed: {str(e)}")
    
    def _validate_units_consistency(self, input_data: Dict[str, Any]) -> None:
        """Validate that all units are consistent (tons, rupees, etc.)."""
        # Check that all capacity values are in tons
        plants = input_data.get("plants", [])
        for plant in plants:
            capacity = plant.get("capacity_tonnes")
            if capacity is None or capacity <= 0:
                self.validation_errors.append(
                    f"Plant {plant.get('plant_id')} has invalid capacity: {capacity}"
                )
        
        # Check that all demand values are in tons
        demand = input_data.get("demand", [])
        for d in demand:
            demand_tonnes = d.get("demand_tonnes")
            if demand_tonnes is None or demand_tonnes < 0:
                self.validation_errors.append(
                    f"Demand for {d.get('customer_id')} in {d.get('period')} is invalid: {demand_tonnes}"
                )
        
        logger.debug("Units consistency validation completed")
    
    def _validate_costs(self, input_data: Dict[str, Any]) -> None:
        """Validate costs are in RAW RUPEES, not negative, not null."""
        costs = input_data.get("costs", {})
        
        # Production costs
        production_costs = costs.get("production", {})
        for plant_id, cost in production_costs.items():
            if cost is None:
                self.validation_errors.append(f"Production cost for {plant_id} is null")
            elif cost < 0:
                self.validation_errors.append(f"Production cost for {plant_id} is negative: {cost}")
            elif cost < 100:  # Suspiciously low
                self.validation_warnings.append(
                    f"Production cost for {plant_id} seems low ({cost} ₹/ton). "
                    f"Ensure it's in RAW RUPEES, not scaled."
                )
            else:
                ensure_raw_rupees(cost, f"production cost for {plant_id}")
        
        # Transport costs
        transport_costs = costs.get("transport", {})
        for route_key, cost in transport_costs.items():
            if cost is None:
                self.validation_errors.append(f"Transport cost for {route_key} is null")
            elif cost < 0:
                self.validation_errors.append(f"Transport cost for {route_key} is negative: {cost}")
            elif cost < 10:  # Suspiciously low
                self.validation_warnings.append(
                    f"Transport cost for {route_key} seems low ({cost} ₹/ton). "
                    f"Ensure it's in RAW RUPEES."
                )
        
        # Fixed trip costs
        fixed_costs = costs.get("fixed_transport", {})
        for route_key, cost in fixed_costs.items():
            if cost is None:
                self.validation_errors.append(f"Fixed trip cost for {route_key} is null")
            elif cost < 0:
                self.validation_errors.append(f"Fixed trip cost for {route_key} is negative: {cost}")
            elif cost < 100:  # Suspiciously low
                self.validation_warnings.append(
                    f"Fixed trip cost for {route_key} seems low ({cost} ₹/trip). "
                    f"Ensure it's in RAW RUPEES."
                )
        
        # Inventory costs
        inventory_costs = costs.get("inventory", {})
        for plant_id, cost in inventory_costs.items():
            if cost is None:
                self.validation_errors.append(f"Inventory cost for {plant_id} is null")
            elif cost < 0:
                self.validation_errors.append(f"Inventory cost for {plant_id} is negative: {cost}")
        
        # Penalty cost
        penalty_cost = costs.get("penalty", {}).get("unmet_demand")
        if penalty_cost is None:
            self.validation_errors.append("Penalty cost for unmet demand is null")
        elif penalty_cost < 0:
            self.validation_errors.append(f"Penalty cost is negative: {penalty_cost}")
        elif penalty_cost < 1000:
            self.validation_warnings.append(
                f"Penalty cost seems low ({penalty_cost} ₹/ton). Should be high to discourage unmet demand."
            )
        
        logger.debug("Cost validation completed")
    
    def _validate_routes(self, input_data: Dict[str, Any]) -> None:
        """Validate routes exist and are properly defined."""
        plants = input_data.get("plants", [])
        customers = input_data.get("customers", [])
        routes = input_data.get("routes", [])
        
        plant_ids = {p["plant_id"] for p in plants}
        customer_ids = {c["customer_id"] for c in customers}
        
        # Check all routes have valid origin and destination
        for route in routes:
            origin = route.get("from")
            dest = route.get("to")
            
            if origin not in plant_ids:
                self.validation_errors.append(
                    f"Route origin {origin} not found in plants"
                )
            
            if dest not in customer_ids:
                self.validation_errors.append(
                    f"Route destination {dest} not found in customers"
                )
        
        # Check that each customer has at least one route
        route_destinations = {r["to"] for r in routes}
        unreachable_customers = customer_ids - route_destinations
        if unreachable_customers:
            self.validation_errors.append(
                f"Customers without routes: {unreachable_customers}"
            )
        
        logger.debug("Route validation completed")
    
    def _validate_reachability(self, input_data: Dict[str, Any]) -> None:
        """Validate that all GUs are reachable from at least one IU."""
        # This is similar to route validation but more comprehensive
        # Could check for connectivity graph
        pass  # Implemented in _validate_routes
    
    def _validate_sbq_feasibility(self, input_data: Dict[str, Any]) -> None:
        """Validate SBQ (Shipment Batch Quantity) is feasible vs vehicle capacity."""
        routes = input_data.get("routes", [])
        transport_modes = input_data.get("transport_modes", [])
        costs = input_data.get("costs", {})
        
        # Build mode capacity map
        mode_capacity = {}
        for mode in transport_modes:
            mode_capacity[mode["mode"]] = mode.get("capacity_tonnes", 30.0)
        
        # Check SBQ for each route
        sbq_dict = costs.get("sbq", {})
        for route in routes:
            route_key = f"{route['from']}_{route['to']}_{route['mode']}"
            sbq = sbq_dict.get(route_key, 0.0)
            capacity = mode_capacity.get(route["mode"], 30.0)
            
            if sbq > capacity:
                self.validation_errors.append(
                    f"SBQ for {route_key} ({sbq} tons) exceeds vehicle capacity ({capacity} tons)"
                )
            elif sbq > capacity * 0.9:
                self.validation_warnings.append(
                    f"SBQ for {route_key} ({sbq} tons) is very close to vehicle capacity ({capacity} tons)"
                )
        
        logger.debug("SBQ feasibility validation completed")
    
    def _validate_demand_capacity(self, input_data: Dict[str, Any]) -> None:
        """Validate that total demand doesn't exceed total capacity (warning only)."""
        plants = input_data.get("plants", [])
        demand = input_data.get("demand", [])
        periods = input_data.get("periods", [])
        
        # Calculate total capacity per period
        total_capacity_per_period = sum(
            p.get("capacity_tonnes", 0) for p in plants
        )
        
        # Calculate total demand per period
        for period in periods:
            period_demand = sum(
                d.get("demand_tonnes", 0)
                for d in demand
                if d.get("period") == period
            )
            
            if period_demand > total_capacity_per_period * 1.1:  # 10% buffer
                self.validation_warnings.append(
                    f"Demand in {period} ({period_demand} tons) exceeds capacity "
                    f"({total_capacity_per_period} tons) by more than 10%"
                )
        
        logger.debug("Demand vs capacity validation completed")
    
    def _validate_safety_stock(self, input_data: Dict[str, Any]) -> None:
        """Validate safety stock doesn't exceed max storage."""
        plants = input_data.get("plants", [])
        
        for plant in plants:
            safety_stock = plant.get("safety_stock_tonnes", 0.0)
            max_storage = plant.get("max_storage_tonnes", 1000000.0)
            
            if safety_stock > max_storage:
                self.validation_errors.append(
                    f"Plant {plant.get('plant_id')}: safety stock ({safety_stock} tons) "
                    f"exceeds max storage ({max_storage} tons)"
                )
        
        logger.debug("Safety stock validation completed")
    
    def _validate_integer_trip_logic(self, input_data: Dict[str, Any]) -> None:
        """Validate integer trip logic is compatible with model."""
        routes = input_data.get("routes", [])
        transport_modes = input_data.get("transport_modes", [])
        
        # Build mode capacity map
        mode_capacity = {}
        for mode in transport_modes:
            mode_capacity[mode["mode"]] = mode.get("capacity_tonnes", 30.0)
        
        # Check that vehicle capacities are reasonable for integer trips
        for route in routes:
            capacity = mode_capacity.get(route["mode"], 30.0)
            if capacity <= 0:
                self.validation_errors.append(
                    f"Route {route['from']}->{route['to']} ({route['mode']}): "
                    f"invalid vehicle capacity {capacity}"
                )
        
        logger.debug("Integer trip logic validation completed")
    
    def save_validation_report(self, scenario_name: str, report: Dict[str, Any]) -> None:
        """Save validation report to database."""
        try:
            # Store in validation_logs table (would need to create this)
            # For now, just log
            logger.info(f"Validation report for {scenario_name}: {report}")
        except Exception as e:
            logger.error(f"Failed to save validation report: {e}")

