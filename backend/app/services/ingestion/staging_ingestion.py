"""
Staging Ingestion Pipeline - PHASE 1 DATA SAFETY

This module implements the safe data ingestion pipeline:
1. Raw CSV/ERP data -> Staging tables (ALWAYS)
2. Validation pipeline validates staging data
3. Only validated data moves to production tables
4. Full transaction management with rollback on failure

CRITICAL: NO production code should read from staging tables.
"""

import pandas as pd
import uuid
import json
from typing import Dict, Any, Optional, List, Type
from datetime import datetime
from fastapi import UploadFile
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
from app.utils.exceptions import DataValidationError
from app.services.audit_service import log_event
import logging

logger = logging.getLogger(__name__)

# Mapping of logical table names to staging models
STAGING_TABLE_MAP = {
    "plant_master": StagingPlantMaster,
    "demand_forecast": StagingDemandForecast,
    "transport_routes_modes": StagingTransportRoutes,
    "production_capacity_cost": StagingProductionCosts,
    "initial_inventory": StagingInitialInventory,
    "safety_stock_policy": StagingSafetyStock,
}

# Required columns for table detection
TABLE_DETECTION_CONFIG = {
    "plant_master": ["plant_id", "plant_name", "plant_type"],
    "demand_forecast": ["customer_node_id", "period", "demand_tonnes"],
    "transport_routes_modes": ["origin_plant_id", "destination_node_id", "transport_mode", "vehicle_capacity_tonnes"],
    "production_capacity_cost": ["plant_id", "period", "max_capacity_tonnes"],
    "initial_inventory": ["node_id", "period", "inventory_tonnes"],
    "safety_stock_policy": ["node_id", "policy_type", "policy_value"],
}


def detect_table_name(df: pd.DataFrame, filename: str, explicit: Optional[str]) -> str:
    """
    Detect target table name from DataFrame columns or filename.
    
    Args:
        df: Input DataFrame
        filename: Source filename
        explicit: Explicitly provided table name
        
    Returns:
        Detected table name
        
    Raises:
        DataValidationError: If table cannot be detected
    """
    if explicit:
        if explicit not in STAGING_TABLE_MAP:
            raise DataValidationError(f"Unknown table_name '{explicit}'. Valid options: {list(STAGING_TABLE_MAP.keys())}")
        return explicit

    # Try filename-based detection
    lowered = filename.lower()
    if "plant" in lowered:
        candidate = "plant_master"
    elif "demand" in lowered:
        candidate = "demand_forecast"
    elif "route" in lowered or "transport" in lowered:
        candidate = "transport_routes_modes"
    elif "production" in lowered or "capacity" in lowered or "cost" in lowered:
        candidate = "production_capacity_cost"
    elif "inventory" in lowered and "safety" not in lowered:
        candidate = "initial_inventory"
    elif "safety" in lowered:
        candidate = "safety_stock_policy"
    else:
        raise DataValidationError(
            f"Could not infer target table from filename '{filename}'. "
            f"Please specify table_name explicitly. Valid options: {list(STAGING_TABLE_MAP.keys())}"
        )

    # Validate that detected table has required columns
    required_columns = TABLE_DETECTION_CONFIG[candidate]
    df_columns = [col.lower().strip() for col in df.columns]
    missing_columns = []
    
    for req_col in required_columns:
        if req_col.lower() not in df_columns:
            missing_columns.append(req_col)
    
    if missing_columns:
        raise DataValidationError(
            f"File appears to target '{candidate}' but is missing required columns: {missing_columns}. "
            f"Available columns: {list(df.columns)}"
        )
    
    return candidate


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to match database schema.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with normalized column names
    """
    # Create a copy to avoid modifying original
    df_normalized = df.copy()
    
    # Convert to lowercase and strip whitespace
    df_normalized.columns = [col.lower().strip().replace(' ', '_') for col in df_normalized.columns]
    
    return df_normalized


async def ingest_to_staging(
    file: UploadFile,
    db: Session,
    table_name: Optional[str] = None,
    user: str = "staging-api"
) -> Dict[str, Any]:
    """
    Ingest uploaded file data into staging tables with full transaction safety.
    
    This is the new SAFE entry point that replaces direct production table writes.
    
    Args:
        file: Uploaded file
        db: Database session
        table_name: Optional explicit table name
        user: User performing the operation
        
    Returns:
        Dictionary with ingestion results
        
    Raises:
        DataValidationError: If file cannot be processed
    """
    if not file.filename:
        raise DataValidationError("File must have a filename")
    
    # Generate unique batch ID for this upload
    batch_id = str(uuid.uuid4())
    
    try:
        # Read file content
        contents = await file.read()
        
        # Parse based on file type
        filename_lower = file.filename.lower()
        if filename_lower.endswith('.csv'):
            df = pd.read_csv(pd.io.common.StringIO(contents.decode('utf-8')))
        elif filename_lower.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(pd.io.common.BytesIO(contents))
        else:
            raise DataValidationError("Unsupported file type. Only CSV and Excel files are supported.")
        
        if df.empty:
            raise DataValidationError("File is empty")
        
        # Normalize column names
        df = normalize_column_names(df)
        
        # Detect target table
        detected_table = detect_table_name(df, file.filename, table_name)
        staging_model = STAGING_TABLE_MAP[detected_table]
        
        # Create validation batch record
        batch_record = ValidationBatch(
            batch_id=batch_id,
            source_file=file.filename,
            table_name=detected_table,
            total_rows=len(df),
            status="pending"
        )
        
        # Begin transaction
        try:
            db.add(batch_record)
            
            # Insert all rows into staging table
            staging_records = []
            for idx, row in df.iterrows():
                # Convert row to dict and add staging metadata
                row_dict = row.to_dict()
                row_dict.update({
                    'batch_id': batch_id,
                    'source_file': file.filename,
                    'source_row': idx + 1,  # 1-based row numbering
                    'validation_status': 'pending'
                })
                
                # Create staging record (let SQLAlchemy handle missing columns)
                staging_record = staging_model(**{k: v for k, v in row_dict.items() 
                                                if hasattr(staging_model, k)})
                staging_records.append(staging_record)
            
            # Bulk insert staging records
            db.add_all(staging_records)
            db.commit()
            
            logger.info(f"Successfully ingested {len(staging_records)} rows to staging table {detected_table} with batch_id {batch_id}")
            
            # Log successful staging
            log_event(
                user=user,
                action="staging_ingestion",
                resource=detected_table,
                details={
                    "batch_id": batch_id,
                    "filename": file.filename,
                    "table": detected_table,
                    "rows_staged": len(staging_records),
                    "status": "success"
                }
            )
            
            return {
                "batch_id": batch_id,
                "filename": file.filename,
                "table": detected_table,
                "rows_staged": len(staging_records),
                "status": "staged",
                "message": f"Data successfully staged. Use batch_id '{batch_id}' to validate and promote to production."
            }
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error during staging ingestion: {e}")
            raise DataValidationError(f"Database error during staging: {str(e)}")
        
    except Exception as e:
        # Log failed staging attempt
        log_event(
            user=user,
            action="staging_ingestion",
            resource=table_name or "unknown",
            details={
                "filename": file.filename,
                "error": str(e),
                "status": "failed"
            }
        )
        
        if isinstance(e, DataValidationError):
            raise
        else:
            logger.error(f"Unexpected error during staging ingestion: {e}")
            raise DataValidationError(f"Failed to stage data: {str(e)}")


def get_staging_summary(db: Session, batch_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get summary of staging data and validation batches.
    
    Args:
        db: Database session
        batch_id: Optional specific batch ID to query
        
    Returns:
        Summary of staging data
    """
    try:
        if batch_id:
            # Get specific batch info
            batch = db.query(ValidationBatch).filter(ValidationBatch.batch_id == batch_id).first()
            if not batch:
                raise DataValidationError(f"Batch {batch_id} not found")
            
            return {
                "batch_id": batch.batch_id,
                "source_file": batch.source_file,
                "table_name": batch.table_name,
                "total_rows": batch.total_rows,
                "valid_rows": batch.valid_rows,
                "invalid_rows": batch.invalid_rows,
                "status": batch.status,
                "created_at": batch.created_at.isoformat() if batch.created_at else None,
                "validated_at": batch.validated_at.isoformat() if batch.validated_at else None,
                "promoted_at": batch.promoted_at.isoformat() if batch.promoted_at else None,
            }
        else:
            # Get summary of all batches
            batches = db.query(ValidationBatch).order_by(ValidationBatch.created_at.desc()).limit(20).all()
            
            return {
                "recent_batches": [
                    {
                        "batch_id": batch.batch_id,
                        "source_file": batch.source_file,
                        "table_name": batch.table_name,
                        "total_rows": batch.total_rows,
                        "status": batch.status,
                        "created_at": batch.created_at.isoformat() if batch.created_at else None,
                    }
                    for batch in batches
                ],
                "total_batches": len(batches)
            }
            
    except Exception as e:
        logger.error(f"Error getting staging summary: {e}")
        raise DataValidationError(f"Failed to get staging summary: {str(e)}")