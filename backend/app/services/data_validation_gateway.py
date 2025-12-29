"""
Data Validation Gateway

Implements strict data quality gating - NO raw or unvalidated data may ever reach the optimization model.
This is the critical control point that enforces the business workflow:

DATA SOURCES → STAGING → CLEAN DATA → MODEL INPUT BUILDER → OPTIMIZATION ENGINE
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
import logging

from app.services.data_validation_service import ValidationResult, _load_data_for_validation
from app.services.data_cleaning_service import DataCleaner
from app.utils.exceptions import DataValidationError, OptimizationError

logger = logging.getLogger(__name__)


class DataValidationGateway:
    """
    Critical gateway that enforces data quality before optimization.
    
    BUSINESS RULE: Optimization can ONLY run when ALL validation stages pass.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.cleaner = DataCleaner()
        
    def validate_and_prepare_optimization_data(self) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Validate all data and prepare clean dataset for optimization.
        
        Returns:
            (is_ready, clean_data, blocking_errors)
            
        CRITICAL: is_ready=False means optimization MUST NOT run.
        """
        try:
            logger.info("Starting comprehensive data validation for optimization")
            
            # Stage 1: Load raw data
            raw_data = _load_data_for_validation(self.db)
            
            # Stage 2: Run 5-stage validation pipeline
            validation_results = self._run_validation_pipeline(raw_data)
            
            # Stage 3: Check if optimization can proceed
            is_ready, blocking_errors = self._assess_optimization_readiness(validation_results)
            
            if not is_ready:
                logger.error(f"Optimization blocked by {len(blocking_errors)} critical errors")
                return False, {}, blocking_errors
            
            # Stage 4: Clean and prepare data
            clean_data = self._prepare_clean_optimization_data(raw_data, validation_results)
            
            logger.info("Data validation passed - optimization ready to proceed")
            return True, clean_data, []
            
        except Exception as e:
            logger.error(f"Data validation gateway failed: {e}")
            return False, {}, [f"Validation system error: {str(e)}"]
    
    def _run_validation_pipeline(self, raw_data: Dict[str, pd.DataFrame]) -> Dict[str, ValidationResult]:
        """Run the complete 5-stage validation pipeline."""
        
        validation_results = {}
        
        # Stage 1: Schema Validation
        validation_results["schema"] = self._validate_schema(raw_data)
        
        # Stage 2: Business Rules Validation
        validation_results["business_rules"] = self._validate_business_rules(raw_data)
        
        # Stage 3: Referential Integrity
        validation_results["referential_integrity"] = self._validate_referential_integrity(raw_data)
        
        # Stage 4: Unit Consistency
        validation_results["unit_consistency"] = self._validate_unit_consistency(raw_data)
        
        # Stage 5: Missing Data Scan
        validation_results["missing_data"] = self._validate_missing_data(raw_data)
        
        return validation_results
    
    def _validate_schema(self, raw_data: Dict[str, pd.DataFrame]) -> ValidationResult:
        """Stage 1: Schema validation - required columns, data types."""
        
        errors = []
        warnings = []
        
        # Required tables
        required_tables = ["plants_df", "production_df", "routes_df", "demand_df"]
        for table in required_tables:
            if table not in raw_data or raw_data[table].empty:
                errors.append({
                    "table": table,
                    "error": "Required table missing or empty",
                    "severity": "CRITICAL"
                })
        
        # Required columns per table
        required_columns = {
            "plants_df": ["plant_id", "plant_name", "plant_type"],
            "production_df": ["plant_id", "period", "max_capacity_tonnes"],
            "routes_df": ["origin_plant_id", "destination_node_id", "transport_mode", "cost_per_tonne"],
            "demand_df": ["customer_node_id", "period", "demand_tonnes"]
        }
        
        for table_name, columns in required_columns.items():
            if table_name in raw_data:
                df = raw_data[table_name]
                for col in columns:
                    if col not in df.columns:
                        errors.append({
                            "table": table_name,
                            "column": col,
                            "error": f"Required column '{col}' missing",
                            "severity": "CRITICAL"
                        })
        
        status = "FAIL" if errors else "PASS"
        return ValidationResult("schema", status, errors, warnings)
    
    def _validate_business_rules(self, raw_data: Dict[str, pd.DataFrame]) -> ValidationResult:
        """Stage 2: Business rules validation."""
        
        errors = []
        warnings = []
        row_level_errors = []
        
        # Validate demand data
        if "demand_df" in raw_data:
            demand_df = raw_data["demand_df"]
            
            # No negative demand
            negative_demand = demand_df[demand_df["demand_tonnes"] < 0]
            for idx, row in negative_demand.iterrows():
                row_level_errors.append({
                    "table": "demand_forecast",
                    "row": idx,
                    "error": f"Negative demand: {row['demand_tonnes']}",
                    "customer": row.get("customer_node_id", "unknown"),
                    "period": row.get("period", "unknown")
                })
            
            # Zero demand warning
            zero_demand = demand_df[demand_df["demand_tonnes"] == 0]
            if len(zero_demand) > 0:
                warnings.append({
                    "table": "demand_forecast",
                    "warning": f"{len(zero_demand)} customers with zero demand",
                    "impact": "May indicate data quality issues"
                })
        
        # Validate production capacity
        if "production_df" in raw_data:
            production_df = raw_data["production_df"]
            
            # No negative capacity
            negative_capacity = production_df[production_df["max_capacity_tonnes"] <= 0]
            for idx, row in negative_capacity.iterrows():
                row_level_errors.append({
                    "table": "production_capacity_cost",
                    "row": idx,
                    "error": f"Invalid capacity: {row['max_capacity_tonnes']}",
                    "plant": row.get("plant_id", "unknown")
                })
        
        # Validate transport routes
        if "routes_df" in raw_data:
            routes_df = raw_data["routes_df"]
            
            # Valid transport modes
            valid_modes = ["road", "rail", "sea", "pipeline"]
            invalid_modes = routes_df[~routes_df["transport_mode"].str.lower().isin(valid_modes)]
            for idx, row in invalid_modes.iterrows():
                row_level_errors.append({
                    "table": "transport_routes_modes",
                    "row": idx,
                    "error": f"Invalid transport mode: {row['transport_mode']}",
                    "route": f"{row.get('origin_plant_id', 'unknown')} -> {row.get('destination_node_id', 'unknown')}"
                })
            
            # Positive costs
            negative_costs = routes_df[routes_df["cost_per_tonne"] <= 0]
            for idx, row in negative_costs.iterrows():
                row_level_errors.append({
                    "table": "transport_routes_modes",
                    "row": idx,
                    "error": f"Invalid cost: {row['cost_per_tonne']}",
                    "route": f"{row.get('origin_plant_id', 'unknown')} -> {row.get('destination_node_id', 'unknown')}"
                })
        
        status = "FAIL" if (errors or len(row_level_errors) > 0) else ("WARN" if warnings else "PASS")
        return ValidationResult("business_rules", status, errors, warnings, row_level_errors)
    
    def _validate_referential_integrity(self, raw_data: Dict[str, pd.DataFrame]) -> ValidationResult:
        """Stage 3: Referential integrity validation."""
        
        errors = []
        warnings = []
        
        if "plants_df" not in raw_data or "routes_df" not in raw_data:
            errors.append({
                "error": "Cannot validate referential integrity - missing core tables",
                "severity": "CRITICAL"
            })
            return ValidationResult("referential_integrity", "FAIL", errors)
        
        plants_df = raw_data["plants_df"]
        routes_df = raw_data["routes_df"]
        
        # Get valid plant IDs
        valid_plant_ids = set(plants_df["plant_id"].unique())
        
        # Check route origins
        invalid_origins = routes_df[~routes_df["origin_plant_id"].isin(valid_plant_ids)]
        if len(invalid_origins) > 0:
            errors.append({
                "table": "transport_routes_modes",
                "error": f"{len(invalid_origins)} routes with invalid origin plant IDs",
                "invalid_ids": invalid_origins["origin_plant_id"].unique().tolist()
            })
        
        # Check route destinations (should exist as plants or customers)
        # For now, assume destinations can be any node
        
        status = "FAIL" if errors else ("WARN" if warnings else "PASS")
        return ValidationResult("referential_integrity", status, errors, warnings)
    
    def _validate_unit_consistency(self, raw_data: Dict[str, pd.DataFrame]) -> ValidationResult:
        """Stage 4: Unit consistency validation."""
        
        errors = []
        warnings = []
        
        # Check for unit mixing in demand (should all be tonnes)
        if "demand_df" in raw_data:
            demand_df = raw_data["demand_df"]
            
            # Check for suspiciously large values (might be in kg instead of tonnes)
            large_demand = demand_df[demand_df["demand_tonnes"] > 100000]  # > 100K tonnes per period
            if len(large_demand) > 0:
                warnings.append({
                    "table": "demand_forecast",
                    "warning": f"{len(large_demand)} demand values > 100K tonnes",
                    "suggestion": "Verify units - might be in kg instead of tonnes"
                })
            
            # Check for suspiciously small values
            small_demand = demand_df[(demand_df["demand_tonnes"] > 0) & (demand_df["demand_tonnes"] < 1)]
            if len(small_demand) > 0:
                warnings.append({
                    "table": "demand_forecast",
                    "warning": f"{len(small_demand)} demand values < 1 tonne",
                    "suggestion": "Verify units - might be in different unit"
                })
        
        status = "WARN" if warnings else "PASS"
        return ValidationResult("unit_consistency", status, errors, warnings)
    
    def _validate_missing_data(self, raw_data: Dict[str, pd.DataFrame]) -> ValidationResult:
        """Stage 5: Missing data scan."""
        
        errors = []
        warnings = []
        
        # Check for missing critical data
        critical_checks = [
            ("plants_df", "plant_id", "Plant ID"),
            ("demand_df", "demand_tonnes", "Demand quantity"),
            ("routes_df", "cost_per_tonne", "Transport cost"),
            ("production_df", "max_capacity_tonnes", "Production capacity")
        ]
        
        for table_name, column, description in critical_checks:
            if table_name in raw_data:
                df = raw_data[table_name]
                if column in df.columns:
                    missing_count = df[column].isna().sum()
                    if missing_count > 0:
                        errors.append({
                            "table": table_name,
                            "column": column,
                            "error": f"{missing_count} missing values in {description}",
                            "severity": "CRITICAL"
                        })
        
        status = "FAIL" if errors else ("WARN" if warnings else "PASS")
        return ValidationResult("missing_data", status, errors, warnings)
    
    def _assess_optimization_readiness(self, validation_results: Dict[str, ValidationResult]) -> Tuple[bool, List[str]]:
        """Assess if optimization can proceed based on validation results."""
        
        blocking_errors = []
        
        # Check each validation stage
        for stage_name, result in validation_results.items():
            if result.status == "FAIL":
                blocking_errors.append(f"{stage_name}: {len(result.errors)} critical errors")
                
                # Add specific error details
                for error in result.errors:
                    if error.get("severity") == "CRITICAL":
                        blocking_errors.append(f"  - {error.get('error', 'Unknown error')}")
        
        # Optimization can only proceed if no FAIL statuses
        is_ready = len(blocking_errors) == 0
        
        return is_ready, blocking_errors
    
    def _prepare_clean_optimization_data(self, raw_data: Dict[str, pd.DataFrame], 
                                       validation_results: Dict[str, ValidationResult]) -> Dict[str, Any]:
        """Prepare clean, validated data for optimization."""
        
        # Clean the data using the data cleaner
        clean_data = self.cleaner.clean_all_data(raw_data)
        
        # Convert to optimization input format
        optimization_data = {
            "plants": clean_data["plants_df"].to_dict("records"),
            "customers": clean_data["demand_df"]["customer_node_id"].unique().tolist(),
            "periods": sorted(clean_data["demand_df"]["period"].unique().tolist()),
            "demand": clean_data["demand_df"].to_dict("records"),
            "capacity": clean_data["production_df"].to_dict("records"),
            "routes": clean_data["routes_df"].to_dict("records"),
            "transport_modes": clean_data["routes_df"]["transport_mode"].unique().tolist()
        }
        
        # Add optional data if available
        if "inventory_df" in clean_data and not clean_data["inventory_df"].empty:
            optimization_data["initial_inventory"] = clean_data["inventory_df"].to_dict("records")
        
        if "safety_stock_df" in clean_data and not clean_data["safety_stock_df"].empty:
            optimization_data["safety_stock"] = clean_data["safety_stock_df"].to_dict("records")
        
        return optimization_data


def check_optimization_readiness(db: Session) -> Dict[str, Any]:
    """
    Public function to check if optimization can run.
    
    Returns comprehensive readiness report.
    """
    gateway = DataValidationGateway(db)
    is_ready, clean_data, blocking_errors = gateway.validate_and_prepare_optimization_data()
    
    return {
        "optimization_ready": is_ready,
        "blocking_errors": blocking_errors,
        "data_available": len(clean_data) > 0,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "READY" if is_ready else "BLOCKED"
    }