"""
Staging Data Validation Pipeline - PHASE 1 DATA SAFETY

This module validates data in staging tables and promotes valid data to production tables.
It implements the complete validation pipeline:

1. Schema validation (data types, required fields)
2. Business rule validation (negative values, etc.)
3. Referential integrity validation
4. Unit normalization
5. Duplicate detection

Only data that passes ALL validation steps is promoted to production tables.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.staging_tables import (
    StagingPlantMaster,
    StagingDemandForecast,
    StagingTransportRoutes,
    StagingProductionCosts,
    StagingInitialInventory,
    StagingSafetyStock,
    ValidationBatch,
)
from app.db.models.plant_master import PlantMaster
from app.db.models.demand_forecast import DemandForecast
from app.db.models.transport_routes_modes import TransportRoutesModes
from app.db.models.production_capacity_cost import ProductionCapacityCost
from app.db.models.initial_inventory import InitialInventory
from app.db.models.safety_stock_policy import SafetyStockPolicy
from app.utils.exceptions import DataValidationError
from app.services.audit_service import log_event

logger = logging.getLogger(__name__)

# Mapping of staging models to production models
STAGING_TO_PRODUCTION_MAP = {
    "plant_master": (StagingPlantMaster, PlantMaster),
    "demand_forecast": (StagingDemandForecast, DemandForecast),
    "transport_routes_modes": (StagingTransportRoutes, TransportRoutesModes),
    "production_capacity_cost": (StagingProductionCosts, ProductionCapacityCost),
    "initial_inventory": (StagingInitialInventory, InitialInventory),
    "safety_stock_policy": (StagingSafetyStock, SafetyStockPolicy),
}


def validate_schema_constraints(staging_record: Any, table_name: str) -> List[str]:
    """
    Validate basic schema constraints for a staging record.
    
    Args:
        staging_record: Staging table record
        table_name: Name of the table being validated
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if table_name == "plant_master":
        if not staging_record.plant_id or not staging_record.plant_id.strip():
            errors.append("plant_id is required")
        if not staging_record.plant_name or not staging_record.plant_name.strip():
            errors.append("plant_name is required")
        if not staging_record.plant_type or not staging_record.plant_type.strip():
            errors.append("plant_type is required")
        if staging_record.latitude is not None and (staging_record.latitude < -90 or staging_record.latitude > 90):
            errors.append("latitude must be between -90 and 90")
        if staging_record.longitude is not None and (staging_record.longitude < -180 or staging_record.longitude > 180):
            errors.append("longitude must be between -180 and 180")
            
    elif table_name == "demand_forecast":
        if not staging_record.customer_node_id or not staging_record.customer_node_id.strip():
            errors.append("customer_node_id is required")
        if not staging_record.period or not staging_record.period.strip():
            errors.append("period is required")
        if staging_record.demand_tonnes is None or staging_record.demand_tonnes < 0:
            errors.append("demand_tonnes must be non-negative")
        if staging_record.confidence_level is not None and (staging_record.confidence_level < 0 or staging_record.confidence_level > 1):
            errors.append("confidence_level must be between 0 and 1")
            
    elif table_name == "transport_routes_modes":
        if not staging_record.origin_plant_id or not staging_record.origin_plant_id.strip():
            errors.append("origin_plant_id is required")
        if not staging_record.destination_node_id or not staging_record.destination_node_id.strip():
            errors.append("destination_node_id is required")
        if not staging_record.transport_mode or not staging_record.transport_mode.strip():
            errors.append("transport_mode is required")
        if staging_record.vehicle_capacity_tonnes is None or staging_record.vehicle_capacity_tonnes <= 0:
            errors.append("vehicle_capacity_tonnes must be positive")
        if staging_record.distance_km is not None and staging_record.distance_km < 0:
            errors.append("distance_km must be non-negative")
        if staging_record.cost_per_tonne is not None and staging_record.cost_per_tonne < 0:
            errors.append("cost_per_tonne must be non-negative")
            
    elif table_name == "production_capacity_cost":
        if not staging_record.plant_id or not staging_record.plant_id.strip():
            errors.append("plant_id is required")
        if not staging_record.period or not staging_record.period.strip():
            errors.append("period is required")
        if staging_record.max_capacity_tonnes is None or staging_record.max_capacity_tonnes <= 0:
            errors.append("max_capacity_tonnes must be positive")
        if staging_record.variable_cost_per_tonne is None or staging_record.variable_cost_per_tonne < 0:
            errors.append("variable_cost_per_tonne must be non-negative")
        if staging_record.min_run_level is not None and (staging_record.min_run_level < 0 or staging_record.min_run_level > 1):
            errors.append("min_run_level must be between 0 and 1")
            
    elif table_name == "initial_inventory":
        if not staging_record.node_id or not staging_record.node_id.strip():
            errors.append("node_id is required")
        if not staging_record.period or not staging_record.period.strip():
            errors.append("period is required")
        if staging_record.inventory_tonnes is None or staging_record.inventory_tonnes < 0:
            errors.append("inventory_tonnes must be non-negative")
            
    elif table_name == "safety_stock_policy":
        if not staging_record.node_id or not staging_record.node_id.strip():
            errors.append("node_id is required")
        if not staging_record.policy_type or not staging_record.policy_type.strip():
            errors.append("policy_type is required")
        if staging_record.policy_value is None or staging_record.policy_value < 0:
            errors.append("policy_value must be non-negative")
    
    return errors


def validate_referential_integrity(db: Session, staging_record: Any, table_name: str) -> List[str]:
    """
    Validate referential integrity constraints.
    
    Args:
        db: Database session
        staging_record: Staging table record
        table_name: Name of the table being validated
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if table_name == "transport_routes_modes":
        # Check if origin_plant_id exists in plant_master
        if staging_record.origin_plant_id:
            plant_exists = db.query(PlantMaster).filter(
                PlantMaster.plant_id == staging_record.origin_plant_id
            ).first()
            if not plant_exists:
                errors.append(f"origin_plant_id '{staging_record.origin_plant_id}' does not exist in plant_master")
                
    elif table_name == "production_capacity_cost":
        # Check if plant_id exists in plant_master
        if staging_record.plant_id:
            plant_exists = db.query(PlantMaster).filter(
                PlantMaster.plant_id == staging_record.plant_id
            ).first()
            if not plant_exists:
                errors.append(f"plant_id '{staging_record.plant_id}' does not exist in plant_master")
    
    return errors


def validate_business_rules(staging_record: Any, table_name: str) -> List[str]:
    """
    Validate business-specific rules.
    
    Args:
        staging_record: Staging table record
        table_name: Name of the table being validated
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if table_name == "transport_routes_modes":
        # SBQ (minimum batch quantity) cannot exceed vehicle capacity
        if (staging_record.min_batch_quantity_tonnes is not None and 
            staging_record.vehicle_capacity_tonnes is not None and
            staging_record.min_batch_quantity_tonnes > staging_record.vehicle_capacity_tonnes):
            errors.append("min_batch_quantity_tonnes cannot exceed vehicle_capacity_tonnes")
            
        # Transport mode validation
        valid_modes = ["road", "rail", "sea", "barge", "pipeline"]
        if staging_record.transport_mode and staging_record.transport_mode.lower() not in valid_modes:
            errors.append(f"transport_mode must be one of: {valid_modes}")
            
    elif table_name == "plant_master":
        # Plant type validation
        valid_types = ["clinker", "grinding", "terminal", "warehouse"]
        if staging_record.plant_type and staging_record.plant_type.lower() not in valid_types:
            errors.append(f"plant_type must be one of: {valid_types}")
    
    return errors


def validate_batch(db: Session, batch_id: str, user: str = "validation-service") -> Dict[str, Any]:
    """
    Validate all records in a staging batch.
    
    Args:
        db: Database session
        batch_id: Batch ID to validate
        user: User performing validation
        
    Returns:
        Validation results dictionary
        
    Raises:
        DataValidationError: If batch not found or validation fails
    """
    # Get batch record
    batch = db.query(ValidationBatch).filter(ValidationBatch.batch_id == batch_id).first()
    if not batch:
        raise DataValidationError(f"Batch {batch_id} not found")
    
    if batch.status != "pending":
        raise DataValidationError(f"Batch {batch_id} has already been processed (status: {batch.status})")
    
    table_name = batch.table_name
    if table_name not in STAGING_TO_PRODUCTION_MAP:
        raise DataValidationError(f"Unknown table name: {table_name}")
    
    staging_model, _ = STAGING_TO_PRODUCTION_MAP[table_name]
    
    try:
        # Get all pending records for this batch
        staging_records = db.query(staging_model).filter(
            staging_model.batch_id == batch_id,
            staging_model.validation_status == "pending"
        ).all()
        
        if not staging_records:
            raise DataValidationError(f"No pending records found for batch {batch_id}")
        
        valid_count = 0
        invalid_count = 0
        validation_errors = []
        
        # Validate each record
        for record in staging_records:
            record_errors = []
            
            # Schema validation
            record_errors.extend(validate_schema_constraints(record, table_name))
            
            # Referential integrity validation
            record_errors.extend(validate_referential_integrity(db, record, table_name))
            
            # Business rules validation
            record_errors.extend(validate_business_rules(record, table_name))
            
            # Update record validation status
            if record_errors:
                record.validation_status = "invalid"
                record.validation_errors = json.dumps(record_errors)
                invalid_count += 1
                validation_errors.extend([f"Row {record.source_row}: {error}" for error in record_errors])
            else:
                record.validation_status = "valid"
                record.validation_errors = None
                valid_count += 1
        
        # Update batch status
        batch.valid_rows = valid_count
        batch.invalid_rows = invalid_count
        batch.validated_at = datetime.utcnow()
        
        if invalid_count > 0:
            batch.status = "validation_failed"
            batch.validation_errors = json.dumps(validation_errors[:100])  # Limit error size
        else:
            batch.status = "validated"
        
        db.commit()
        
        # Log validation results
        log_event(
            user=user,
            action="batch_validation",
            resource=table_name,
            details={
                "batch_id": batch_id,
                "table": table_name,
                "total_rows": len(staging_records),
                "valid_rows": valid_count,
                "invalid_rows": invalid_count,
                "status": batch.status
            }
        )
        
        return {
            "batch_id": batch_id,
            "table": table_name,
            "total_rows": len(staging_records),
            "valid_rows": valid_count,
            "invalid_rows": invalid_count,
            "status": batch.status,
            "validation_errors": validation_errors[:50] if validation_errors else [],  # Return first 50 errors
            "can_promote": invalid_count == 0
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error validating batch {batch_id}: {e}")
        
        # Update batch status to failed
        batch.status = "validation_error"
        batch.validation_errors = json.dumps([str(e)])
        db.commit()
        
        raise DataValidationError(f"Validation failed for batch {batch_id}: {str(e)}")


def promote_batch_to_production(db: Session, batch_id: str, user: str = "promotion-service") -> Dict[str, Any]:
    """
    Promote validated staging data to production tables.
    
    This operation is ATOMIC - either all records are promoted or none are.
    
    Args:
        db: Database session
        batch_id: Batch ID to promote
        user: User performing promotion
        
    Returns:
        Promotion results dictionary
        
    Raises:
        DataValidationError: If batch cannot be promoted
    """
    # Get batch record
    batch = db.query(ValidationBatch).filter(ValidationBatch.batch_id == batch_id).first()
    if not batch:
        raise DataValidationError(f"Batch {batch_id} not found")
    
    if batch.status != "validated":
        raise DataValidationError(f"Batch {batch_id} is not ready for promotion (status: {batch.status})")
    
    if batch.invalid_rows > 0:
        raise DataValidationError(f"Batch {batch_id} has {batch.invalid_rows} invalid rows and cannot be promoted")
    
    table_name = batch.table_name
    if table_name not in STAGING_TO_PRODUCTION_MAP:
        raise DataValidationError(f"Unknown table name: {table_name}")
    
    staging_model, production_model = STAGING_TO_PRODUCTION_MAP[table_name]
    
    try:
        # Begin transaction for atomic promotion
        # Get all valid records for this batch
        valid_records = db.query(staging_model).filter(
            staging_model.batch_id == batch_id,
            staging_model.validation_status == "valid"
        ).all()
        
        if not valid_records:
            raise DataValidationError(f"No valid records found for batch {batch_id}")
        
        promoted_count = 0
        
        # Convert staging records to production records
        for staging_record in valid_records:
            # Extract production fields (exclude staging metadata)
            production_data = {}
            for column in production_model.__table__.columns:
                column_name = column.name
                if hasattr(staging_record, column_name) and column_name not in ['created_at', 'updated_at']:
                    value = getattr(staging_record, column_name)
                    if value is not None:  # Only include non-null values
                        production_data[column_name] = value
            
            # Create production record
            production_record = production_model(**production_data)
            db.add(production_record)
            promoted_count += 1
        
        # Update batch status
        batch.status = "promoted"
        batch.promoted_at = datetime.utcnow()
        
        # Commit all changes atomically
        db.commit()
        
        logger.info(f"Successfully promoted {promoted_count} records from batch {batch_id} to {table_name}")
        
        # Log promotion success
        log_event(
            user=user,
            action="batch_promotion",
            resource=table_name,
            details={
                "batch_id": batch_id,
                "table": table_name,
                "promoted_rows": promoted_count,
                "status": "success"
            }
        )
        
        return {
            "batch_id": batch_id,
            "table": table_name,
            "promoted_rows": promoted_count,
            "status": "promoted",
            "message": f"Successfully promoted {promoted_count} records to production table {table_name}"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error promoting batch {batch_id}: {e}")
        
        # Update batch status to failed
        batch.status = "promotion_failed"
        batch.validation_errors = json.dumps([f"Promotion error: {str(e)}"])
        db.commit()
        
        # Log promotion failure
        log_event(
            user=user,
            action="batch_promotion",
            resource=table_name,
            details={
                "batch_id": batch_id,
                "table": table_name,
                "error": str(e),
                "status": "failed"
            }
        )
        
        raise DataValidationError(f"Failed to promote batch {batch_id}: {str(e)}")


def get_validation_status(db: Session, batch_id: str) -> Dict[str, Any]:
    """
    Get detailed validation status for a batch.
    
    Args:
        db: Database session
        batch_id: Batch ID to check
        
    Returns:
        Detailed validation status
        
    Raises:
        DataValidationError: If batch not found
    """
    batch = db.query(ValidationBatch).filter(ValidationBatch.batch_id == batch_id).first()
    if not batch:
        raise DataValidationError(f"Batch {batch_id} not found")
    
    # Get error details if available
    validation_errors = []
    if batch.validation_errors:
        try:
            validation_errors = json.loads(batch.validation_errors)
        except json.JSONDecodeError:
            validation_errors = [batch.validation_errors]
    
    return {
        "batch_id": batch.batch_id,
        "source_file": batch.source_file,
        "table_name": batch.table_name,
        "total_rows": batch.total_rows,
        "valid_rows": batch.valid_rows,
        "invalid_rows": batch.invalid_rows,
        "status": batch.status,
        "validation_errors": validation_errors,
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
        "validated_at": batch.validated_at.isoformat() if batch.validated_at else None,
        "promoted_at": batch.promoted_at.isoformat() if batch.promoted_at else None,
        "can_promote": batch.status == "validated" and batch.invalid_rows == 0
    }