"""
Data Health Status Service

Provides comprehensive data quality monitoring and validation status
for all tables required by the optimization engine.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import pandas as pd
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


class DataHealthStatus:
    """Data health status for a single table."""
    
    def __init__(
        self,
        table_name: str,
        record_count: int = 0,
        last_update: Optional[datetime] = None,
        validation_status: str = "UNKNOWN",
        missing_key_fields: int = 0,
        referential_integrity_issues: int = 0,
        validation_errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None
    ):
        self.table_name = table_name
        self.record_count = record_count
        self.last_update = last_update
        self.validation_status = validation_status  # PASS, WARN, FAIL
        self.missing_key_fields = missing_key_fields
        self.referential_integrity_issues = referential_integrity_issues
        self.validation_errors = validation_errors or []
        self.warnings = warnings or []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_name": self.table_name,
            "record_count": self.record_count,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "validation_status": self.validation_status,
            "missing_key_fields": self.missing_key_fields,
            "referential_integrity_issues": self.referential_integrity_issues,
            "validation_errors": self.validation_errors,
            "warnings": self.warnings
        }


def _get_table_stats(db: Session, model_class, table_name: str) -> Dict[str, Any]:
    """Get basic statistics for a table."""
    try:
        count = db.query(model_class).count()
        
        # Get last update timestamp if available
        last_update = None
        if hasattr(model_class, 'updated_at'):
            result = db.query(func.max(model_class.updated_at)).scalar()
            last_update = result
        elif hasattr(model_class, 'created_at'):
            result = db.query(func.max(model_class.created_at)).scalar()
            last_update = result
            
        return {
            "count": count,
            "last_update": last_update
        }
    except Exception as e:
        logger.error(f"Error getting stats for {table_name}: {e}")
        return {"count": 0, "last_update": None}


def _validate_plant_master(db: Session) -> DataHealthStatus:
    """Validate plant_master table."""
    stats = _get_table_stats(db, PlantMaster, "plant_master")
    errors = []
    warnings = []
    
    try:
        # Check for missing key fields
        plants = db.query(PlantMaster).all()
        missing_key_fields = 0
        
        for plant in plants:
            if not plant.plant_id or not plant.plant_name or not plant.plant_type:
                missing_key_fields += 1
        
        # Check for duplicate plant_ids
        plant_ids = [p.plant_id for p in plants]
        if len(plant_ids) != len(set(plant_ids)):
            errors.append("Duplicate plant_id values detected")
        
        # Warnings for missing geographic data
        missing_coords = sum(1 for p in plants if p.latitude is None or p.longitude is None)
        if missing_coords > 0:
            warnings.append(f"{missing_coords} plants missing geographic coordinates")
        
        status = "FAIL" if errors else ("WARN" if warnings else "PASS")
        
        return DataHealthStatus(
            table_name="plant_master",
            record_count=stats["count"],
            last_update=stats["last_update"],
            validation_status=status,
            missing_key_fields=missing_key_fields,
            validation_errors=errors,
            warnings=warnings
        )
        
    except Exception as e:
        logger.error(f"Error validating plant_master: {e}")
        return DataHealthStatus(
            table_name="plant_master",
            record_count=stats["count"],
            last_update=stats["last_update"],
            validation_status="FAIL",
            validation_errors=[f"Validation failed: {str(e)}"]
        )


def _validate_production_capacity_cost(db: Session) -> DataHealthStatus:
    """Validate production_capacity_cost table."""
    stats = _get_table_stats(db, ProductionCapacityCost, "production_capacity_cost")
    errors = []
    warnings = []
    
    try:
        records = db.query(ProductionCapacityCost).all()
        missing_key_fields = 0
        
        for record in records:
            if (not record.plant_id or not record.period or 
                record.max_capacity_tonnes is None or record.variable_cost_per_tonne is None):
                missing_key_fields += 1
            
            # Business rule validations
            if record.max_capacity_tonnes is not None and record.max_capacity_tonnes <= 0:
                errors.append(f"Non-positive capacity for plant {record.plant_id}, period {record.period}")
            
            if record.variable_cost_per_tonne is not None and record.variable_cost_per_tonne < 0:
                errors.append(f"Negative production cost for plant {record.plant_id}, period {record.period}")
        
        # Check referential integrity with plant_master
        plant_ids = {r.plant_id for r in records}
        existing_plants = {p.plant_id for p in db.query(PlantMaster.plant_id).all()}
        missing_plants = plant_ids - existing_plants
        ri_issues = len(missing_plants)
        
        if missing_plants:
            errors.append(f"plant_id not found in plant_master: {', '.join(sorted(missing_plants))}")
        
        status = "FAIL" if errors else ("WARN" if warnings else "PASS")
        
        return DataHealthStatus(
            table_name="production_capacity_cost",
            record_count=stats["count"],
            last_update=stats["last_update"],
            validation_status=status,
            missing_key_fields=missing_key_fields,
            referential_integrity_issues=ri_issues,
            validation_errors=errors,
            warnings=warnings
        )
        
    except Exception as e:
        logger.error(f"Error validating production_capacity_cost: {e}")
        return DataHealthStatus(
            table_name="production_capacity_cost",
            record_count=stats["count"],
            last_update=stats["last_update"],
            validation_status="FAIL",
            validation_errors=[f"Validation failed: {str(e)}"]
        )


def _validate_transport_routes_modes(db: Session) -> DataHealthStatus:
    """Validate transport_routes_modes table."""
    stats = _get_table_stats(db, TransportRoutesModes, "transport_routes_modes")
    errors = []
    warnings = []
    
    try:
        records = db.query(TransportRoutesModes).all()
        missing_key_fields = 0
        
        for record in records:
            if (not record.origin_plant_id or not record.destination_node_id or 
                not record.transport_mode or record.vehicle_capacity_tonnes is None):
                missing_key_fields += 1
            
            # Business rule validations
            if record.vehicle_capacity_tonnes is not None and record.vehicle_capacity_tonnes <= 0:
                errors.append(f"Non-positive vehicle capacity for route {record.origin_plant_id} -> {record.destination_node_id}")
            
            if record.origin_plant_id == record.destination_node_id:
                errors.append(f"Illegal route: origin equals destination ({record.origin_plant_id})")
            
            # Check for valid transport modes
            valid_modes = {"road", "rail", "sea", "barge", "pipeline"}
            if record.transport_mode and record.transport_mode.lower() not in valid_modes:
                warnings.append(f"Unknown transport mode: {record.transport_mode}")
        
        # Check referential integrity
        origin_plant_ids = {r.origin_plant_id for r in records}
        existing_plants = {p.plant_id for p in db.query(PlantMaster.plant_id).all()}
        missing_origins = origin_plant_ids - existing_plants
        ri_issues = len(missing_origins)
        
        if missing_origins:
            errors.append(f"origin_plant_id not found in plant_master: {', '.join(sorted(missing_origins))}")
        
        status = "FAIL" if errors else ("WARN" if warnings else "PASS")
        
        return DataHealthStatus(
            table_name="transport_routes_modes",
            record_count=stats["count"],
            last_update=stats["last_update"],
            validation_status=status,
            missing_key_fields=missing_key_fields,
            referential_integrity_issues=ri_issues,
            validation_errors=errors,
            warnings=warnings
        )
        
    except Exception as e:
        logger.error(f"Error validating transport_routes_modes: {e}")
        return DataHealthStatus(
            table_name="transport_routes_modes",
            record_count=stats["count"],
            last_update=stats["last_update"],
            validation_status="FAIL",
            validation_errors=[f"Validation failed: {str(e)}"]
        )


def _validate_demand_forecast(db: Session) -> DataHealthStatus:
    """Validate demand_forecast table."""
    stats = _get_table_stats(db, DemandForecast, "demand_forecast")
    errors = []
    warnings = []
    
    try:
        records = db.query(DemandForecast).all()
        missing_key_fields = 0
        
        for record in records:
            if (not record.customer_node_id or not record.period or 
                record.demand_tonnes is None):
                missing_key_fields += 1
            
            # Business rule validations
            if record.demand_tonnes is not None and record.demand_tonnes < 0:
                errors.append(f"Negative demand for customer {record.customer_node_id}, period {record.period}")
        
        # Check for duplicate (customer, period) combinations
        customer_periods = [(r.customer_node_id, r.period) for r in records]
        if len(customer_periods) != len(set(customer_periods)):
            errors.append("Duplicate (customer_node_id, period) combinations detected")
        
        status = "FAIL" if errors else ("WARN" if warnings else "PASS")
        
        return DataHealthStatus(
            table_name="demand_forecast",
            record_count=stats["count"],
            last_update=stats["last_update"],
            validation_status=status,
            missing_key_fields=missing_key_fields,
            validation_errors=errors,
            warnings=warnings
        )
        
    except Exception as e:
        logger.error(f"Error validating demand_forecast: {e}")
        return DataHealthStatus(
            table_name="demand_forecast",
            record_count=stats["count"],
            last_update=stats["last_update"],
            validation_status="FAIL",
            validation_errors=[f"Validation failed: {str(e)}"]
        )


def _validate_initial_inventory(db: Session) -> DataHealthStatus:
    """Validate initial_inventory table."""
    stats = _get_table_stats(db, InitialInventory, "initial_inventory")
    errors = []
    warnings = []
    
    try:
        records = db.query(InitialInventory).all()
        missing_key_fields = 0
        
        for record in records:
            if (not record.node_id or not record.period or 
                record.inventory_tonnes is None):
                missing_key_fields += 1
            
            # Business rule validations
            if record.inventory_tonnes is not None and record.inventory_tonnes < 0:
                errors.append(f"Negative inventory for node {record.node_id}, period {record.period}")
        
        status = "FAIL" if errors else ("WARN" if warnings else "PASS")
        
        return DataHealthStatus(
            table_name="initial_inventory",
            record_count=stats["count"],
            last_update=stats["last_update"],
            validation_status=status,
            missing_key_fields=missing_key_fields,
            validation_errors=errors,
            warnings=warnings
        )
        
    except Exception as e:
        logger.error(f"Error validating initial_inventory: {e}")
        return DataHealthStatus(
            table_name="initial_inventory",
            record_count=stats["count"],
            last_update=stats["last_update"],
            validation_status="FAIL",
            validation_errors=[f"Validation failed: {str(e)}"]
        )


def _validate_safety_stock_policy(db: Session) -> DataHealthStatus:
    """Validate safety_stock_policy table."""
    stats = _get_table_stats(db, SafetyStockPolicy, "safety_stock_policy")
    errors = []
    warnings = []
    
    try:
        records = db.query(SafetyStockPolicy).all()
        missing_key_fields = 0
        
        for record in records:
            if (not record.node_id or not record.policy_type or 
                record.policy_value is None):
                missing_key_fields += 1
            
            # Business rule validations
            if record.safety_stock_tonnes is not None and record.safety_stock_tonnes < 0:
                errors.append(f"Negative safety stock for node {record.node_id}")
            
            if record.max_inventory_tonnes is not None and record.max_inventory_tonnes < 0:
                errors.append(f"Negative max inventory for node {record.node_id}")
            
            # Check valid policy types
            valid_policies = {"days_of_cover", "percentage_of_demand", "absolute"}
            if record.policy_type and record.policy_type not in valid_policies:
                warnings.append(f"Unknown policy type: {record.policy_type}")
        
        status = "FAIL" if errors else ("WARN" if warnings else "PASS")
        
        return DataHealthStatus(
            table_name="safety_stock_policy",
            record_count=stats["count"],
            last_update=stats["last_update"],
            validation_status=status,
            missing_key_fields=missing_key_fields,
            validation_errors=errors,
            warnings=warnings
        )
        
    except Exception as e:
        logger.error(f"Error validating safety_stock_policy: {e}")
        return DataHealthStatus(
            table_name="safety_stock_policy",
            record_count=stats["count"],
            last_update=stats["last_update"],
            validation_status="FAIL",
            validation_errors=[f"Validation failed: {str(e)}"]
        )


def get_data_health_overview(db: Session) -> Dict[str, Any]:
    """
    Get comprehensive data health status for all tables.
    
    Returns:
        Dict containing:
        - table_status: Dict of table name -> DataHealthStatus
        - overall_status: PASS/WARN/FAIL
        - optimization_ready: bool
        - summary: Dict with counts
    """
    
    # Validate each table
    table_validators = {
        "plant_master": _validate_plant_master,
        "production_capacity_cost": _validate_production_capacity_cost,
        "transport_routes_modes": _validate_transport_routes_modes,
        "demand_forecast": _validate_demand_forecast,
        "initial_inventory": _validate_initial_inventory,
        "safety_stock_policy": _validate_safety_stock_policy
    }
    
    table_status = {}
    for table_name, validator in table_validators.items():
        try:
            status = validator(db)
            table_status[table_name] = status.to_dict()
        except Exception as e:
            logger.error(f"Failed to validate {table_name}: {e}")
            table_status[table_name] = DataHealthStatus(
                table_name=table_name,
                validation_status="FAIL",
                validation_errors=[f"Validation failed: {str(e)}"]
            ).to_dict()
    
    # Determine overall status
    statuses = [status["validation_status"] for status in table_status.values()]
    if "FAIL" in statuses:
        overall_status = "FAIL"
    elif "WARN" in statuses:
        overall_status = "WARN"
    else:
        overall_status = "PASS"
    
    # Check if optimization is ready (no FAIL status)
    optimization_ready = "FAIL" not in statuses
    
    # Summary statistics
    total_records = sum(status["record_count"] for status in table_status.values())
    total_errors = sum(len(status["validation_errors"]) for status in table_status.values())
    total_warnings = sum(len(status["warnings"]) for status in table_status.values())
    
    return {
        "table_status": table_status,
        "overall_status": overall_status,
        "optimization_ready": optimization_ready,
        "summary": {
            "total_tables": len(table_status),
            "total_records": total_records,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "tables_passing": sum(1 for s in statuses if s == "PASS"),
            "tables_warning": sum(1 for s in statuses if s == "WARN"),
            "tables_failing": sum(1 for s in statuses if s == "FAIL")
        },
        "timestamp": datetime.utcnow().isoformat()
    }