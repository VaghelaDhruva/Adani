"""
Comprehensive Data Validation Service

Implements the 5-stage validation pipeline required before optimization:
1. Schema validation
2. Business rule validation  
3. Referential integrity
4. Unit consistency
5. Missing data scan
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
import logging

from app.db.models.plant_master import PlantMaster
from app.db.models.production_capacity_cost import ProductionCapacityCost
from app.db.models.transport_routes_modes import TransportRoutesModes
from app.db.models.demand_forecast import DemandForecast
from app.db.models.initial_inventory import InitialInventory
from app.db.models.safety_stock_policy import SafetyStockPolicy
from app.services.validation.validators import validate_referential_integrity
from app.services.validation.rules import reject_negative_demand, reject_illegal_routes, enforce_unit_consistency
from app.utils.exceptions import DataValidationError

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of a validation stage."""
    
    def __init__(
        self,
        stage: str,
        status: str,  # PASS, WARN, FAIL
        errors: Optional[List[Dict[str, Any]]] = None,
        warnings: Optional[List[Dict[str, Any]]] = None,
        row_level_errors: Optional[List[Dict[str, Any]]] = None
    ):
        self.stage = stage
        self.status = status
        self.errors = errors or []
        self.warnings = warnings or []
        self.row_level_errors = row_level_errors or []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "status": self.status,
            "errors": self.errors,
            "warnings": self.warnings,
            "row_level_errors": self.row_level_errors,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "row_error_count": len(self.row_level_errors)
        }


def _load_data_for_validation(db: Session) -> Dict[str, pd.DataFrame]:
    """Load all data tables as DataFrames for validation."""
    
    try:
        # Plant master
        plants_df = pd.DataFrame([
            {
                "plant_id": p.plant_id,
                "plant_name": p.plant_name,
                "plant_type": p.plant_type,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "region": p.region,
                "country": p.country
            }
            for p in db.query(PlantMaster).all()
        ])
        
        # Production capacity
        production_df = pd.DataFrame([
            {
                "plant_id": r.plant_id,
                "period": r.period,
                "max_capacity_tonnes": r.max_capacity_tonnes,
                "variable_cost_per_tonne": r.variable_cost_per_tonne,
                "fixed_cost_per_period": r.fixed_cost_per_period,
                "min_run_level": r.min_run_level
            }
            for r in db.query(ProductionCapacityCost).all()
        ])
        
        # Transport routes
        routes_df = pd.DataFrame([
            {
                "origin_plant_id": r.origin_plant_id,
                "destination_node_id": r.destination_node_id,
                "transport_mode": r.transport_mode,
                "distance_km": r.distance_km,
                "cost_per_tonne": r.cost_per_tonne,
                "cost_per_tonne_km": r.cost_per_tonne_km,
                "fixed_cost_per_trip": r.fixed_cost_per_trip,
                "vehicle_capacity_tonnes": r.vehicle_capacity_tonnes,
                "min_batch_quantity_tonnes": r.min_batch_quantity_tonnes,
                "lead_time_days": r.lead_time_days,
                "is_active": r.is_active
            }
            for r in db.query(TransportRoutesModes).all()
        ])
        
        # Demand forecast
        demand_df = pd.DataFrame([
            {
                "customer_node_id": d.customer_node_id,
                "period": d.period,
                "demand_tonnes": d.demand_tonnes,
                "demand_low_tonnes": d.demand_low_tonnes,
                "demand_high_tonnes": d.demand_high_tonnes,
                "confidence_level": d.confidence_level,
                "source": d.source
            }
            for d in db.query(DemandForecast).all()
        ])
        
        # Initial inventory
        inventory_df = pd.DataFrame([
            {
                "node_id": inv.node_id,
                "period": inv.period,
                "inventory_tonnes": inv.inventory_tonnes
            }
            for inv in db.query(InitialInventory).all()
        ])
        
        # Safety stock policy
        safety_stock_df = pd.DataFrame([
            {
                "node_id": s.node_id,
                "policy_type": s.policy_type,
                "policy_value": s.policy_value,
                "safety_stock_tonnes": s.safety_stock_tonnes,
                "max_inventory_tonnes": s.max_inventory_tonnes
            }
            for s in db.query(SafetyStockPolicy).all()
        ])
        
        return {
            "plants": plants_df,
            "production_capacity_cost": production_df,
            "transport_routes_modes": routes_df,
            "demand_forecast": demand_df,
            "initial_inventory": inventory_df,
            "safety_stock_policy": safety_stock_df
        }
        
    except Exception as e:
        logger.error(f"Error loading data for validation: {e}")
        raise DataValidationError(f"Failed to load data: {str(e)}")


def _validate_stage1_schema(data: Dict[str, pd.DataFrame]) -> ValidationResult:
    """Stage 1: Schema validation - required columns exist, data types correct."""
    
    errors = []
    warnings = []
    
    # Define required columns for each table
    required_columns = {
        "plants": ["plant_id", "plant_name", "plant_type"],
        "production_capacity_cost": ["plant_id", "period", "max_capacity_tonnes", "variable_cost_per_tonne"],
        "transport_routes_modes": ["origin_plant_id", "destination_node_id", "transport_mode", "vehicle_capacity_tonnes"],
        "demand_forecast": ["customer_node_id", "period", "demand_tonnes"],
        "initial_inventory": ["node_id", "period", "inventory_tonnes"],
        "safety_stock_policy": ["node_id", "policy_type", "policy_value"]
    }
    
    for table_name, df in data.items():
        if table_name not in required_columns:
            continue
            
        required_cols = required_columns[table_name]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            errors.append({
                "table": table_name,
                "type": "missing_columns",
                "message": f"Missing required columns: {', '.join(missing_cols)}",
                "columns": missing_cols
            })
        
        # Check data types for numeric columns
        numeric_columns = {
            "plants": [],
            "production_capacity_cost": ["max_capacity_tonnes", "variable_cost_per_tonne"],
            "transport_routes_modes": ["vehicle_capacity_tonnes", "distance_km", "cost_per_tonne"],
            "demand_forecast": ["demand_tonnes"],
            "initial_inventory": ["inventory_tonnes"],
            "safety_stock_policy": ["policy_value", "safety_stock_tonnes"]
        }
        
        if table_name in numeric_columns:
            for col in numeric_columns[table_name]:
                if col in df.columns:
                    non_numeric = df[col].apply(lambda x: x is not None and not isinstance(x, (int, float))).sum()
                    if non_numeric > 0:
                        warnings.append({
                            "table": table_name,
                            "column": col,
                            "type": "data_type",
                            "message": f"Column {col} has {non_numeric} non-numeric values",
                            "count": int(non_numeric)
                        })
    
    status = "FAIL" if errors else ("WARN" if warnings else "PASS")
    return ValidationResult("schema_validation", status, errors, warnings)


def _validate_stage2_business_rules(data: Dict[str, pd.DataFrame]) -> ValidationResult:
    """Stage 2: Business rule validation."""
    
    errors = []
    warnings = []
    row_level_errors = []
    
    try:
        # Rule 1: No negative demand
        if not data["demand_forecast"].empty:
            negative_demand = data["demand_forecast"][data["demand_forecast"]["demand_tonnes"] < 0]
            for idx, row in negative_demand.iterrows():
                row_level_errors.append({
                    "table": "demand_forecast",
                    "row_index": int(idx),
                    "rule": "no_negative_demand",
                    "message": f"Negative demand: {row['demand_tonnes']} for customer {row['customer_node_id']}, period {row['period']}",
                    "customer_node_id": row["customer_node_id"],
                    "period": row["period"],
                    "value": float(row["demand_tonnes"])
                })
        
        # Rule 2: Production capacity > 0
        if not data["production_capacity_cost"].empty:
            zero_capacity = data["production_capacity_cost"][data["production_capacity_cost"]["max_capacity_tonnes"] <= 0]
            for idx, row in zero_capacity.iterrows():
                row_level_errors.append({
                    "table": "production_capacity_cost",
                    "row_index": int(idx),
                    "rule": "positive_capacity",
                    "message": f"Non-positive capacity: {row['max_capacity_tonnes']} for plant {row['plant_id']}, period {row['period']}",
                    "plant_id": row["plant_id"],
                    "period": row["period"],
                    "value": float(row["max_capacity_tonnes"])
                })
        
        # Rule 3: Valid transport mode values
        if not data["transport_routes_modes"].empty:
            valid_modes = {"road", "rail", "sea", "barge", "pipeline"}
            invalid_modes = data["transport_routes_modes"][
                ~data["transport_routes_modes"]["transport_mode"].str.lower().isin(valid_modes)
            ]
            for idx, row in invalid_modes.iterrows():
                warnings.append({
                    "table": "transport_routes_modes",
                    "row_index": int(idx),
                    "rule": "valid_transport_mode",
                    "message": f"Unknown transport mode: {row['transport_mode']}",
                    "transport_mode": row["transport_mode"]
                })
        
        # Rule 4: No duplicate keys per (node, period)
        for table_name, key_cols in [
            ("demand_forecast", ["customer_node_id", "period"]),
            ("production_capacity_cost", ["plant_id", "period"]),
            ("initial_inventory", ["node_id", "period"])
        ]:
            if table_name in data and not data[table_name].empty:
                df = data[table_name]
                duplicates = df[df.duplicated(subset=key_cols, keep=False)]
                if not duplicates.empty:
                    errors.append({
                        "table": table_name,
                        "type": "duplicate_keys",
                        "message": f"Duplicate keys found in {table_name}",
                        "count": len(duplicates),
                        "key_columns": key_cols
                    })
        
        # Rule 5: SBQ <= vehicle capacity
        if not data["transport_routes_modes"].empty:
            df = data["transport_routes_modes"]
            invalid_sbq = df[
                (df["min_batch_quantity_tonnes"].notna()) & 
                (df["vehicle_capacity_tonnes"].notna()) &
                (df["min_batch_quantity_tonnes"] > df["vehicle_capacity_tonnes"])
            ]
            for idx, row in invalid_sbq.iterrows():
                row_level_errors.append({
                    "table": "transport_routes_modes",
                    "row_index": int(idx),
                    "rule": "sbq_capacity_constraint",
                    "message": f"SBQ ({row['min_batch_quantity_tonnes']}) > vehicle capacity ({row['vehicle_capacity_tonnes']})",
                    "origin_plant_id": row["origin_plant_id"],
                    "destination_node_id": row["destination_node_id"],
                    "sbq": float(row["min_batch_quantity_tonnes"]),
                    "capacity": float(row["vehicle_capacity_tonnes"])
                })
        
        # Rule 6: Costs must be positive
        cost_checks = [
            ("production_capacity_cost", "variable_cost_per_tonne"),
            ("transport_routes_modes", "cost_per_tonne"),
            ("transport_routes_modes", "cost_per_tonne_km")
        ]
        
        for table_name, cost_col in cost_checks:
            if table_name in data and not data[table_name].empty:
                df = data[table_name]
                if cost_col in df.columns:
                    negative_costs = df[(df[cost_col].notna()) & (df[cost_col] < 0)]
                    for idx, row in negative_costs.iterrows():
                        row_level_errors.append({
                            "table": table_name,
                            "row_index": int(idx),
                            "rule": "positive_costs",
                            "message": f"Negative cost: {row[cost_col]} in column {cost_col}",
                            "column": cost_col,
                            "value": float(row[cost_col])
                        })
        
    except Exception as e:
        errors.append({
            "type": "validation_error",
            "message": f"Business rule validation failed: {str(e)}"
        })
    
    status = "FAIL" if errors or row_level_errors else ("WARN" if warnings else "PASS")
    return ValidationResult("business_rules", status, errors, warnings, row_level_errors)


def _validate_stage3_referential_integrity(db: Session, data: Dict[str, pd.DataFrame]) -> ValidationResult:
    """Stage 3: Referential integrity checks."""
    
    errors = []
    warnings = []
    
    try:
        # Check plant_id references in production_capacity_cost
        if not data["production_capacity_cost"].empty:
            prod_plant_ids = set(data["production_capacity_cost"]["plant_id"].unique())
            existing_plant_ids = set(data["plants"]["plant_id"].unique()) if not data["plants"].empty else set()
            missing_plants = prod_plant_ids - existing_plant_ids
            
            if missing_plants:
                errors.append({
                    "type": "foreign_key_violation",
                    "table": "production_capacity_cost",
                    "column": "plant_id",
                    "message": f"plant_id not found in plant_master: {', '.join(sorted(missing_plants))}",
                    "missing_values": sorted(list(missing_plants))
                })
        
        # Check origin_plant_id references in transport_routes_modes
        if not data["transport_routes_modes"].empty:
            route_plant_ids = set(data["transport_routes_modes"]["origin_plant_id"].unique())
            existing_plant_ids = set(data["plants"]["plant_id"].unique()) if not data["plants"].empty else set()
            missing_origins = route_plant_ids - existing_plant_ids
            
            if missing_origins:
                errors.append({
                    "type": "foreign_key_violation",
                    "table": "transport_routes_modes",
                    "column": "origin_plant_id",
                    "message": f"origin_plant_id not found in plant_master: {', '.join(sorted(missing_origins))}",
                    "missing_values": sorted(list(missing_origins))
                })
        
        # Check destination_node_id references (should be plants or customers)
        if not data["transport_routes_modes"].empty:
            dest_node_ids = set(data["transport_routes_modes"]["destination_node_id"].unique())
            plant_ids = set(data["plants"]["plant_id"].unique()) if not data["plants"].empty else set()
            customer_ids = set(data["demand_forecast"]["customer_node_id"].unique()) if not data["demand_forecast"].empty else set()
            known_nodes = plant_ids | customer_ids
            
            if known_nodes:  # Only check if we have reference data
                missing_destinations = dest_node_ids - known_nodes
                if missing_destinations:
                    warnings.append({
                        "type": "unknown_destination",
                        "table": "transport_routes_modes",
                        "column": "destination_node_id",
                        "message": f"destination_node_id not found in known plants/customers: {', '.join(sorted(missing_destinations))}",
                        "missing_values": sorted(list(missing_destinations))
                    })
        
        # Check node_id references in inventory and safety stock
        for table_name, node_col in [("initial_inventory", "node_id"), ("safety_stock_policy", "node_id")]:
            if table_name in data and not data[table_name].empty:
                node_ids = set(data[table_name][node_col].unique())
                plant_ids = set(data["plants"]["plant_id"].unique()) if not data["plants"].empty else set()
                customer_ids = set(data["demand_forecast"]["customer_node_id"].unique()) if not data["demand_forecast"].empty else set()
                known_nodes = plant_ids | customer_ids
                
                if known_nodes:  # Only check if we have reference data
                    missing_nodes = node_ids - known_nodes
                    if missing_nodes:
                        warnings.append({
                            "type": "unknown_node",
                            "table": table_name,
                            "column": node_col,
                            "message": f"{node_col} not found in known plants/customers: {', '.join(sorted(missing_nodes))}",
                            "missing_values": sorted(list(missing_nodes))
                        })
        
    except Exception as e:
        errors.append({
            "type": "validation_error",
            "message": f"Referential integrity validation failed: {str(e)}"
        })
    
    status = "FAIL" if errors else ("WARN" if warnings else "PASS")
    return ValidationResult("referential_integrity", status, errors, warnings)


def _validate_stage4_unit_consistency(data: Dict[str, pd.DataFrame]) -> ValidationResult:
    """Stage 4: Unit consistency checks."""
    
    errors = []
    warnings = []
    
    try:
        # Check for mixed units in demand (should all be tonnes)
        if not data["demand_forecast"].empty:
            # Look for obvious unit inconsistencies in magnitude
            demand_values = data["demand_forecast"]["demand_tonnes"].dropna()
            if not demand_values.empty:
                min_val, max_val = demand_values.min(), demand_values.max()
                if max_val > 0 and (max_val / min_val > 10000):  # Suspicious range
                    warnings.append({
                        "type": "unit_inconsistency",
                        "table": "demand_forecast",
                        "column": "demand_tonnes",
                        "message": f"Suspicious demand range: {min_val:.2f} to {max_val:.2f} tonnes (possible unit mixing)",
                        "min_value": float(min_val),
                        "max_value": float(max_val)
                    })
        
        # Check distance units (should be km)
        if not data["transport_routes_modes"].empty:
            distances = data["transport_routes_modes"]["distance_km"].dropna()
            if not distances.empty:
                # Distances > 50,000 km are suspicious (Earth circumference ~40,000 km)
                suspicious_distances = distances[distances > 50000]
                if not suspicious_distances.empty:
                    warnings.append({
                        "type": "unit_inconsistency",
                        "table": "transport_routes_modes",
                        "column": "distance_km",
                        "message": f"Suspicious distances > 50,000 km detected (possible unit mixing)",
                        "count": len(suspicious_distances),
                        "max_distance": float(suspicious_distances.max())
                    })
        
        # Check cost consistency (look for orders of magnitude differences)
        cost_columns = [
            ("production_capacity_cost", "variable_cost_per_tonne"),
            ("transport_routes_modes", "cost_per_tonne"),
            ("transport_routes_modes", "cost_per_tonne_km")
        ]
        
        for table_name, cost_col in cost_columns:
            if table_name in data and not data[table_name].empty:
                df = data[table_name]
                if cost_col in df.columns:
                    costs = df[cost_col].dropna()
                    if not costs.empty and costs.min() > 0:
                        cost_range = costs.max() / costs.min()
                        if cost_range > 100000:  # 5 orders of magnitude difference
                            warnings.append({
                                "type": "unit_inconsistency",
                                "table": table_name,
                                "column": cost_col,
                                "message": f"Large cost range in {cost_col}: {costs.min():.2f} to {costs.max():.2f} (possible unit mixing)",
                                "min_cost": float(costs.min()),
                                "max_cost": float(costs.max()),
                                "range_ratio": float(cost_range)
                            })
        
    except Exception as e:
        errors.append({
            "type": "validation_error",
            "message": f"Unit consistency validation failed: {str(e)}"
        })
    
    status = "FAIL" if errors else ("WARN" if warnings else "PASS")
    return ValidationResult("unit_consistency", status, errors, warnings)


def _validate_stage5_missing_data(data: Dict[str, pd.DataFrame]) -> ValidationResult:
    """Stage 5: Missing data scan."""
    
    errors = []
    warnings = []
    
    try:
        # Critical missing data that blocks optimization
        critical_checks = [
            ("plants", "plant_id", "No plants defined"),
            ("demand_forecast", "demand_tonnes", "No demand data"),
            ("production_capacity_cost", "max_capacity_tonnes", "No production capacity data")
        ]
        
        for table_name, column, message in critical_checks:
            if table_name not in data or data[table_name].empty:
                errors.append({
                    "type": "missing_critical_data",
                    "table": table_name,
                    "message": message,
                    "severity": "critical"
                })
            elif column in data[table_name].columns:
                missing_count = data[table_name][column].isna().sum()
                total_count = len(data[table_name])
                if missing_count == total_count:
                    errors.append({
                        "type": "missing_critical_data",
                        "table": table_name,
                        "column": column,
                        "message": f"All values missing in critical column {column}",
                        "severity": "critical"
                    })
                elif missing_count > 0:
                    warnings.append({
                        "type": "missing_data",
                        "table": table_name,
                        "column": column,
                        "message": f"{missing_count}/{total_count} missing values in {column}",
                        "missing_count": int(missing_count),
                        "total_count": int(total_count),
                        "missing_percentage": float(missing_count / total_count * 100)
                    })
        
        # Check for missing periods (gaps in time series)
        if not data["demand_forecast"].empty:
            periods = sorted(data["demand_forecast"]["period"].unique())
            if len(periods) > 1:
                # Simple gap detection for numeric periods
                try:
                    numeric_periods = [int(p) for p in periods if str(p).isdigit()]
                    if len(numeric_periods) > 1:
                        expected_periods = list(range(min(numeric_periods), max(numeric_periods) + 1))
                        missing_periods = set(expected_periods) - set(numeric_periods)
                        if missing_periods:
                            warnings.append({
                                "type": "missing_periods",
                                "table": "demand_forecast",
                                "message": f"Missing periods in demand forecast: {sorted(missing_periods)}",
                                "missing_periods": sorted(list(missing_periods))
                            })
                except ValueError:
                    # Non-numeric periods, skip gap detection
                    pass
        
        # Check for orphaned data (routes without corresponding plants/demand)
        if not data["transport_routes_modes"].empty and not data["plants"].empty:
            route_origins = set(data["transport_routes_modes"]["origin_plant_id"].unique())
            existing_plants = set(data["plants"]["plant_id"].unique())
            orphaned_routes = route_origins - existing_plants
            
            if orphaned_routes:
                warnings.append({
                    "type": "orphaned_data",
                    "table": "transport_routes_modes",
                    "message": f"Routes reference non-existent plants: {', '.join(sorted(orphaned_routes))}",
                    "orphaned_plants": sorted(list(orphaned_routes))
                })
        
    except Exception as e:
        errors.append({
            "type": "validation_error",
            "message": f"Missing data validation failed: {str(e)}"
        })
    
    status = "FAIL" if errors else ("WARN" if warnings else "PASS")
    return ValidationResult("missing_data_scan", status, errors, warnings)


def run_comprehensive_validation(db: Session) -> Dict[str, Any]:
    """
    Run the complete 5-stage validation pipeline.
    
    Returns:
        Dict containing:
        - stages: List of ValidationResult dicts
        - overall_status: PASS/WARN/FAIL
        - optimization_ready: bool
        - summary: Aggregated counts
        - error_report_csv: CSV-formatted error report
    """
    
    try:
        # Load data
        data = _load_data_for_validation(db)
        
        # Run all validation stages
        stages = [
            _validate_stage1_schema(data),
            _validate_stage2_business_rules(data),
            _validate_stage3_referential_integrity(db, data),
            _validate_stage4_unit_consistency(data),
            _validate_stage5_missing_data(data)
        ]
        
        # Convert to dicts
        stage_results = [stage.to_dict() for stage in stages]
        
        # Determine overall status
        statuses = [stage.status for stage in stages]
        if "FAIL" in statuses:
            overall_status = "FAIL"
        elif "WARN" in statuses:
            overall_status = "WARN"
        else:
            overall_status = "PASS"
        
        # Optimization ready if no FAIL status
        optimization_ready = "FAIL" not in statuses
        
        # Summary statistics
        total_errors = sum(len(stage.errors) + len(stage.row_level_errors) for stage in stages)
        total_warnings = sum(len(stage.warnings) for stage in stages)
        
        # Generate CSV error report
        error_report_rows = []
        for stage in stages:
            for error in stage.errors:
                error_report_rows.append({
                    "stage": stage.stage,
                    "type": "error",
                    "table": error.get("table", ""),
                    "column": error.get("column", ""),
                    "row_index": error.get("row_index", ""),
                    "message": error.get("message", ""),
                    "severity": "error"
                })
            for error in stage.row_level_errors:
                error_report_rows.append({
                    "stage": stage.stage,
                    "type": "row_error",
                    "table": error.get("table", ""),
                    "column": error.get("column", ""),
                    "row_index": error.get("row_index", ""),
                    "message": error.get("message", ""),
                    "severity": "error"
                })
            for warning in stage.warnings:
                error_report_rows.append({
                    "stage": stage.stage,
                    "type": "warning",
                    "table": warning.get("table", ""),
                    "column": warning.get("column", ""),
                    "row_index": warning.get("row_index", ""),
                    "message": warning.get("message", ""),
                    "severity": "warning"
                })
        
        # Convert to CSV string
        if error_report_rows:
            error_df = pd.DataFrame(error_report_rows)
            error_report_csv = error_df.to_csv(index=False)
        else:
            error_report_csv = "stage,type,table,column,row_index,message,severity\n"
        
        return {
            "stages": stage_results,
            "overall_status": overall_status,
            "optimization_ready": optimization_ready,
            "summary": {
                "total_stages": len(stages),
                "stages_passing": sum(1 for s in statuses if s == "PASS"),
                "stages_warning": sum(1 for s in statuses if s == "WARN"),
                "stages_failing": sum(1 for s in statuses if s == "FAIL"),
                "total_errors": total_errors,
                "total_warnings": total_warnings
            },
            "error_report_csv": error_report_csv,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Comprehensive validation failed: {e}")
        return {
            "stages": [],
            "overall_status": "FAIL",
            "optimization_ready": False,
            "summary": {
                "total_stages": 0,
                "stages_passing": 0,
                "stages_warning": 0,
                "stages_failing": 1,
                "total_errors": 1,
                "total_warnings": 0
            },
            "error_report_csv": f"stage,type,table,column,row_index,message,severity\nvalidation_pipeline,error,,,,'Validation pipeline failed: {str(e)}',error\n",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }