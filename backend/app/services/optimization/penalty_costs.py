"""
Penalty cost modeling for service failures and constraint violations.
Adds configurable penalties to the optimization objective and reporting.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import pandas as pd

from app.core.config import get_settings


class PenaltyType(Enum):
    UNMET_DEMAND = "unmet_demand"
    STOCKOUT = "stockout"
    SAFETY_STOCK_VIOLATION = "safety_stock_violation"
    CAPACITY_VIOLATION = "capacity_violation"
    LATE_DELIVERY = "late_delivery"


class PenaltyCostModel:
    """
    Models penalty costs for various service failures and constraint violations.
    Integrates with the optimization model and reporting layer.
    """
    
    def __init__(self, penalty_config: Optional[Dict[str, float]] = None):
        """
        Initialize penalty cost model.
        
        Args:
            penalty_config: Dict mapping penalty types to cost per unit
        """
        settings = get_settings()
        
        # Default penalty costs (can be overridden by config)
        self.penalty_costs = {
            PenaltyType.UNMET_DEMAND.value: 1000.0,  # $ per tonne of unmet demand
            PenaltyType.STOCKOUT.value: 500.0,       # $ per stockout event
            PenaltyType.SAFETY_STOCK_VIOLATION.value: 100.0,  # $ per tonne below safety stock
            PenaltyType.CAPACITY_VIOLATION.value: 200.0,       # $ per tonne over capacity
            PenaltyType.LATE_DELIVERY.value: 50.0,              # $ per period late
        }
        
        # Update with provided config
        if penalty_config:
            self.penalty_costs.update(penalty_config)
        
        # Track penalty calculations
        self.penalty_breakdown = {}
    
    def calculate_penalties(self, solution: Dict[str, Any], model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate all penalty costs for a given solution.
        
        Args:
            solution: Optimization solution results
            model_data: Original model input data
            
        Returns:
            Dict with penalty cost breakdown and total
        """
        penalties = {
            "unmet_demand_penalty": self._calculate_unmet_demand_penalty(solution, model_data),
            "stockout_penalty": self._calculate_stockout_penalty(solution, model_data),
            "safety_stock_violation_penalty": self._calculate_safety_stock_penalty(solution, model_data),
            "capacity_violation_penalty": self._calculate_capacity_violation_penalty(solution, model_data),
            "late_delivery_penalty": self._calculate_late_delivery_penalty(solution, model_data),
        }
        
        # Calculate total penalty
        total_penalty = sum(penalties.values())
        penalties["total_penalty"] = total_penalty
        
        # Store breakdown for reporting
        self.penalty_breakdown = penalties.copy()
        
        return penalties
    
    def _calculate_unmet_demand_penalty(self, solution: Dict[str, Any], model_data: Dict[str, Any]) -> float:
        """Calculate penalty for unmet demand."""
        penalty = 0.0
        penalty_rate = self.penalty_costs[PenaltyType.UNMET_DEMAND.value]
        
        # Get demand data
        demand_df = model_data["demand_forecast"]
        shipments = solution.get("shipments", [])
        
        # Create shipment lookup
        shipment_lookup = {}
        for shipment in shipments:
            key = (shipment["destination"], shipment["period"])
            shipment_lookup[key] = shipment_lookup.get(key, 0) + shipment["tonnes"]
        
        # Calculate unmet demand
        for _, demand_row in demand_df.iterrows():
            customer = demand_row["customer_node_id"]
            period = demand_row["period"]
            required_demand = demand_row["demand_tonnes"]
            
            actual_shipment = shipment_lookup.get((customer, period), 0)
            unmet_demand = max(0, required_demand - actual_shipment)
            
            penalty += unmet_demand * penalty_rate
        
        return penalty
    
    def _calculate_stockout_penalty(self, solution: Dict[str, Any], model_data: Dict[str, Any]) -> float:
        """Calculate penalty for stockout events."""
        penalty = 0.0
        penalty_rate = self.penalty_costs[PenaltyType.STOCKOUT.value]
        
        # Get inventory data
        inventory = solution.get("inventory", [])
        safety_stock_df = model_data.get("safety_stock_policy", pd.DataFrame())
        
        # Create safety stock lookup
        ss_lookup = {}
        if not safety_stock_df.empty:
            for _, ss_row in safety_stock_df.iterrows():
                node = ss_row["node_id"]
                ss_lookup[node] = ss_row.get("safety_stock_tonnes", 0)
        
        # Count stockout events
        stockout_events = 0
        for inv in inventory:
            plant = inv["plant"]
            period = inv["period"]
            inventory_level = inv["tonnes"]
            safety_stock = ss_lookup.get(plant, 0)
            
            if inventory_level < safety_stock:
                stockout_events += 1
        
        penalty = stockout_events * penalty_rate
        return penalty
    
    def _calculate_safety_stock_violation_penalty(self, solution: Dict[str, Any], model_data: Dict[str, Any]) -> float:
        """Calculate penalty for safety stock violations (per tonne)."""
        penalty = 0.0
        penalty_rate = self.penalty_costs[PenaltyType.SAFETY_STOCK_VIOLATION.value]
        
        # Get inventory data
        inventory = solution.get("inventory", [])
        safety_stock_df = model_data.get("safety_stock_policy", pd.DataFrame())
        
        # Create safety stock lookup
        ss_lookup = {}
        if not safety_stock_df.empty:
            for _, ss_row in safety_stock_df.iterrows():
                node = ss_row["node_id"]
                ss_lookup[node] = ss_row.get("safety_stock_tonnes", 0)
        
        # Calculate safety stock violations
        for inv in inventory:
            plant = inv["plant"]
            period = inv["period"]
            inventory_level = inv["tonnes"]
            safety_stock = ss_lookup.get(plant, 0)
            
            if inventory_level < safety_stock:
                violation_amount = safety_stock - inventory_level
                penalty += violation_amount * penalty_rate
        
        return penalty
    
    def _calculate_capacity_violation_penalty(self, solution: Dict[str, Any], model_data: Dict[str, Any]) -> float:
        """Calculate penalty for capacity violations."""
        penalty = 0.0
        penalty_rate = self.penalty_costs[PenaltyType.CAPACITY_VIOLATION.value]
        
        # Get production and capacity data
        production = solution.get("production", [])
        capacity_df = model_data["production_capacity_cost"]
        
        # Create capacity lookup
        cap_lookup = {}
        for _, cap_row in capacity_df.iterrows():
            key = f"{cap_row['plant_id']}_{cap_row['period']}"
            cap_lookup[key] = cap_row.get("max_capacity_tonnes", 0)
        
        # Calculate capacity violations
        for prod in production:
            plant = prod["plant"]
            period = prod["period"]
            actual_production = prod["tonnes"]
            
            key = f"{plant}_{period}"
            max_capacity = cap_lookup.get(key, 0)
            
            if actual_production > max_capacity:
                violation_amount = actual_production - max_capacity
                penalty += violation_amount * penalty_rate
        
        return penalty
    
    def _calculate_late_delivery_penalty(self, solution: Dict[str, Any], model_data: Dict[str, Any]) -> float:
        """
        Calculate penalty for late deliveries.
        This is a simplified implementation - in practice would need delivery schedule data.
        """
        penalty = 0.0
        penalty_rate = self.penalty_costs[PenaltyType.LATE_DELIVERY.value]
        
        # Simplified: assume all shipments are on time for now
        # In a full implementation, would compare actual vs required delivery periods
        
        return penalty
    
    def get_penalty_summary(self) -> Dict[str, Any]:
        """
        Get summary of penalty costs for reporting.
        """
        if not self.penalty_breakdown:
            return {"message": "No penalty calculations available"}
        
        total_penalty = self.penalty_breakdown.get("total_penalty", 0)
        
        # Calculate percentage breakdown
        summary = {
            "total_penalty_cost": total_penalty,
            "penalty_breakdown": {},
            "dominant_penalty_type": None,
            "penalty_recommendations": []
        }
        
        # Calculate percentages
        for penalty_type, amount in self.penalty_breakdown.items():
            if penalty_type != "total_penalty" and amount > 0:
                percentage = (amount / total_penalty) * 100 if total_penalty > 0 else 0
                summary["penalty_breakdown"][penalty_type] = {
                    "amount": amount,
                    "percentage": percentage
                }
        
        # Find dominant penalty type
        if summary["penalty_breakdown"]:
            dominant = max(summary["penalty_breakdown"].items(), key=lambda x: x[1]["amount"])
            summary["dominant_penalty_type"] = dominant[0]
        
        # Generate recommendations
        summary["penalty_recommendations"] = self._generate_penalty_recommendations()
        
        return summary
    
    def _generate_penalty_recommendations(self) -> List[str]:
        """Generate recommendations based on penalty analysis."""
        recommendations = []
        
        if not self.penalty_breakdown:
            return recommendations
        
        # Unmet demand recommendations
        unmet_penalty = self.penalty_breakdown.get("unmet_demand_penalty", 0)
        if unmet_penalty > 0:
            recommendations.append(
                f"High unmet demand penalty (${unmet_penalty:.2f}). "
                "Consider increasing production capacity or adding backup suppliers."
            )
        
        # Safety stock recommendations
        ss_penalty = self.penalty_breakdown.get("safety_stock_violation_penalty", 0)
        if ss_penalty > 0:
            recommendations.append(
                f"Safety stock violations costing ${ss_penalty:.2f}. "
                "Review safety stock policies or increase safety stock levels."
            )
        
        # Capacity violation recommendations
        cap_penalty = self.penalty_breakdown.get("capacity_violation_penalty", 0)
        if cap_penalty > 0:
            recommendations.append(
                f"Capacity violations costing ${cap_penalty:.2f}. "
                "Consider capacity expansion or better production planning."
            )
        
        # Stockout recommendations
        stockout_penalty = self.penalty_breakdown.get("stockout_penalty", 0)
        if stockout_penalty > 0:
            recommendations.append(
                f"Stockout events costing ${stockout_penalty:.2f}. "
                "Improve demand forecasting and inventory management."
            )
        
        return recommendations
    
    def update_penalty_config(self, new_config: Dict[str, float]) -> None:
        """
        Update penalty cost configuration.
        
        Args:
            new_config: New penalty costs to apply
        """
        self.penalty_costs.update(new_config)
    
    def get_penalty_config(self) -> Dict[str, float]:
        """Get current penalty cost configuration."""
        return self.penalty_costs.copy()
    
    def validate_penalty_config(self) -> Dict[str, Any]:
        """
        Validate penalty cost configuration.
        
        Returns:
            Dict with validation results
        """
        issues = []
        
        for penalty_type, cost in self.penalty_costs.items():
            if cost < 0:
                issues.append(f"Negative penalty cost for {penalty_type}: {cost}")
            if cost == 0:
                issues.append(f"Zero penalty cost for {penalty_type} - may not incentivize compliance")
            if cost > 10000:  # Arbitrary high threshold
                issues.append(f"Very high penalty cost for {penalty_type}: {cost}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "total_issues": len(issues)
        }
