"""
Clean Data Service

Provides cleaned, validated, and normalized data views for the optimization model.
This service ensures that ONLY clean data reaches the optimization engine.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
from sqlalchemy.orm import Session
import logging

from app.db.models.plant_master import PlantMaster
from app.db.models.production_capacity_cost import ProductionCapacityCost
from app.db.models.transport_routes_modes import TransportRoutesModes
from app.db.models.demand_forecast import DemandForecast
from app.db.models.initial_inventory import InitialInventory
from app.db.models.safety_stock_policy import SafetyStockPolicy
from app.services.data_validation_service import run_comprehensive_validation
from app.utils.exceptions import DataValidationError

logger = logging.getLogger(__name__)


def _clean_and_normalize_plants(db: Session) -> pd.DataFrame:
    """Load and clean plant master data."""
    
    plants = db.query(PlantMaster).all()
    
    df = pd.DataFrame([
        {
            "plant_id": p.plant_id.strip().upper() if p.plant_id else None,
            "plant_name": p.plant_name.strip() if p.plant_name else None,
            "plant_type": p.plant_type.strip().lower() if p.plant_type else None,
            "latitude": float(p.latitude) if p.latitude is not None else None,
            "longitude": float(p.longitude) if p.longitude is not None else None,
            "region": p.region.strip() if p.region else None,
            "country": p.country.strip() if p.country else None
        }
        for p in plants
    ])
    
    # Remove rows with missing critical fields
    df = df.dropna(subset=["plant_id", "plant_name", "plant_type"])
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["plant_id"])
    
    logger.info(f"Cleaned plant_master: {len(df)} records")
    return df


def _clean_and_normalize_production_capacity(db: Session) -> pd.DataFrame:
    """Load and clean production capacity data."""
    
    records = db.query(ProductionCapacityCost).all()
    
    df = pd.DataFrame([
        {
            "plant_id": r.plant_id.strip().upper() if r.plant_id else None,
            "period": str(r.period).strip() if r.period else None,
            "max_capacity_tonnes": float(r.max_capacity_tonnes) if r.max_capacity_tonnes is not None else 0.0,
            "variable_cost_per_tonne": float(r.variable_cost_per_tonne) if r.variable_cost_per_tonne is not None else 0.0,
            "fixed_cost_per_period": float(r.fixed_cost_per_period) if r.fixed_cost_per_period is not None else 0.0,
            "min_run_level": float(r.min_run_level) if r.min_run_level is not None else 0.0,
            "holding_cost_per_tonne": 10.0  # Default holding cost
        }
        for r in records
    ])
    
    # Remove rows with missing critical fields
    df = df.dropna(subset=["plant_id", "period"])
    
    # Remove rows with non-positive capacity
    df = df[df["max_capacity_tonnes"] > 0]
    
    # Remove rows with negative costs
    df = df[df["variable_cost_per_tonne"] >= 0]
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["plant_id", "period"])
    
    logger.info(f"Cleaned production_capacity_cost: {len(df)} records")
    return df


def _clean_and_normalize_transport_routes(db: Session) -> pd.DataFrame:
    """Load and clean transport routes data."""
    
    records = db.query(TransportRoutesModes).filter(
        TransportRoutesModes.is_active == "Y"
    ).all()
    
    df = pd.DataFrame([
        {
            "origin_plant_id": r.origin_plant_id.strip().upper() if r.origin_plant_id else None,
            "destination_node_id": r.destination_node_id.strip().upper() if r.destination_node_id else None,
            "transport_mode": r.transport_mode.strip().lower() if r.transport_mode else None,
            "distance_km": float(r.distance_km) if r.distance_km is not None else 100.0,  # Default distance
            "cost_per_tonne": float(r.cost_per_tonne) if r.cost_per_tonne is not None else 0.0,
            "cost_per_tonne_km": float(r.cost_per_tonne_km) if r.cost_per_tonne_km is not None else 0.1,  # Default rate
            "fixed_cost_per_trip": float(r.fixed_cost_per_trip) if r.fixed_cost_per_trip is not None else 0.0,
            "vehicle_capacity_tonnes": float(r.vehicle_capacity_tonnes) if r.vehicle_capacity_tonnes is not None else 25.0,
            "min_batch_quantity_tonnes": float(r.min_batch_quantity_tonnes) if r.min_batch_quantity_tonnes is not None else 0.0,
            "lead_time_days": float(r.lead_time_days) if r.lead_time_days is not None else 1.0
        }
        for r in records
    ])
    
    # Remove rows with missing critical fields
    df = df.dropna(subset=["origin_plant_id", "destination_node_id", "transport_mode"])
    
    # Remove illegal routes (origin == destination)
    df = df[df["origin_plant_id"] != df["destination_node_id"]]
    
    # Remove rows with non-positive vehicle capacity
    df = df[df["vehicle_capacity_tonnes"] > 0]
    
    # Ensure SBQ <= vehicle capacity
    df.loc[df["min_batch_quantity_tonnes"] > df["vehicle_capacity_tonnes"], "min_batch_quantity_tonnes"] = df["vehicle_capacity_tonnes"]
    
    # Calculate total transport cost per tonne
    df["total_cost_per_tonne"] = df["cost_per_tonne"] + (df["cost_per_tonne_km"] * df["distance_km"])
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["origin_plant_id", "destination_node_id", "transport_mode"])
    
    logger.info(f"Cleaned transport_routes_modes: {len(df)} records")
    return df


def _clean_and_normalize_demand_forecast(db: Session) -> pd.DataFrame:
    """Load and clean demand forecast data."""
    
    records = db.query(DemandForecast).all()
    
    df = pd.DataFrame([
        {
            "customer_node_id": r.customer_node_id.strip().upper() if r.customer_node_id else None,
            "period": str(r.period).strip() if r.period else None,
            "demand_tonnes": float(r.demand_tonnes) if r.demand_tonnes is not None else 0.0,
            "demand_low_tonnes": float(r.demand_low_tonnes) if r.demand_low_tonnes is not None else None,
            "demand_high_tonnes": float(r.demand_high_tonnes) if r.demand_high_tonnes is not None else None,
            "confidence_level": float(r.confidence_level) if r.confidence_level is not None else 0.95,
            "source": r.source.strip() if r.source else "unknown"
        }
        for r in records
    ])
    
    # Remove rows with missing critical fields
    df = df.dropna(subset=["customer_node_id", "period"])
    
    # Remove rows with negative demand
    df = df[df["demand_tonnes"] >= 0]
    
    # Remove duplicates (keep first occurrence)
    df = df.drop_duplicates(subset=["customer_node_id", "period"])
    
    logger.info(f"Cleaned demand_forecast: {len(df)} records")
    return df


def _clean_and_normalize_initial_inventory(db: Session) -> pd.DataFrame:
    """Load and clean initial inventory data."""
    
    records = db.query(InitialInventory).all()
    
    df = pd.DataFrame([
        {
            "node_id": r.node_id.strip().upper() if r.node_id else None,
            "period": str(r.period).strip() if r.period else None,
            "inventory_tonnes": float(r.inventory_tonnes) if r.inventory_tonnes is not None else 0.0
        }
        for r in records
    ])
    
    # Remove rows with missing critical fields
    df = df.dropna(subset=["node_id", "period"])
    
    # Remove rows with negative inventory
    df = df[df["inventory_tonnes"] >= 0]
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["node_id", "period"])
    
    logger.info(f"Cleaned initial_inventory: {len(df)} records")
    return df


def _clean_and_normalize_safety_stock_policy(db: Session) -> pd.DataFrame:
    """Load and clean safety stock policy data."""
    
    records = db.query(SafetyStockPolicy).all()
    
    df = pd.DataFrame([
        {
            "node_id": r.node_id.strip().upper() if r.node_id else None,
            "policy_type": r.policy_type.strip().lower() if r.policy_type else None,
            "policy_value": float(r.policy_value) if r.policy_value is not None else 0.0,
            "safety_stock_tonnes": float(r.safety_stock_tonnes) if r.safety_stock_tonnes is not None else 0.0,
            "max_inventory_tonnes": float(r.max_inventory_tonnes) if r.max_inventory_tonnes is not None else None
        }
        for r in records
    ])
    
    # Remove rows with missing critical fields
    df = df.dropna(subset=["node_id", "policy_type"])
    
    # Remove rows with negative safety stock
    df = df[df["safety_stock_tonnes"] >= 0]
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["node_id"])
    
    logger.info(f"Cleaned safety_stock_policy: {len(df)} records")
    return df


def get_clean_data_for_optimization(db: Session, validate_first: bool = True) -> Dict[str, Any]:
    """
    Get cleaned and validated data ready for optimization model.
    
    Args:
        db: Database session
        validate_first: If True, run validation first and fail if critical errors found
    
    Returns:
        Dict containing cleaned DataFrames and metadata
    
    Raises:
        DataValidationError: If validation fails and validate_first=True
    """
    
    if validate_first:
        # Run comprehensive validation first
        validation_result = run_comprehensive_validation(db)
        
        if not validation_result["optimization_ready"]:
            error_summary = validation_result["summary"]
            raise DataValidationError(
                f"Data validation failed: {error_summary['total_errors']} errors found. "
                f"Optimization cannot proceed until all critical errors are resolved."
            )
        
        logger.info(f"Data validation passed with {validation_result['summary']['total_warnings']} warnings")
    
    # Load and clean all data tables
    try:
        plants_df = _clean_and_normalize_plants(db)
        production_df = _clean_and_normalize_production_capacity(db)
        routes_df = _clean_and_normalize_transport_routes(db)
        demand_df = _clean_and_normalize_demand_forecast(db)
        inventory_df = _clean_and_normalize_initial_inventory(db)
        safety_stock_df = _clean_and_normalize_safety_stock_policy(db)
        
        # Derive time periods from demand
        time_periods = sorted(demand_df["period"].unique().tolist()) if not demand_df.empty else []
        
        # Final consistency checks
        if plants_df.empty:
            raise DataValidationError("No valid plants found after cleaning")
        
        if demand_df.empty:
            raise DataValidationError("No valid demand data found after cleaning")
        
        if production_df.empty:
            raise DataValidationError("No valid production capacity data found after cleaning")
        
        # Filter production and routes to only include known plants
        known_plant_ids = set(plants_df["plant_id"].unique())
        production_df = production_df[production_df["plant_id"].isin(known_plant_ids)]
        routes_df = routes_df[routes_df["origin_plant_id"].isin(known_plant_ids)]
        
        # Filter inventory and safety stock to only include known nodes
        known_customer_ids = set(demand_df["customer_node_id"].unique())
        known_node_ids = known_plant_ids | known_customer_ids
        inventory_df = inventory_df[inventory_df["node_id"].isin(known_node_ids)]
        safety_stock_df = safety_stock_df[safety_stock_df["node_id"].isin(known_node_ids)]
        
        logger.info("Successfully prepared clean data for optimization")
        
        return {
            "plants": plants_df,
            "production_capacity_cost": production_df,
            "transport_routes_modes": routes_df,
            "demand_forecast": demand_df,
            "initial_inventory": inventory_df,
            "safety_stock_policy": safety_stock_df,
            "time_periods": time_periods,
            "metadata": {
                "total_plants": len(plants_df),
                "total_customers": len(known_customer_ids),
                "total_routes": len(routes_df),
                "total_periods": len(time_periods),
                "data_cleaned_at": pd.Timestamp.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error preparing clean data: {e}")
        raise DataValidationError(f"Failed to prepare clean data: {str(e)}")


def get_clean_data_preview(db: Session, table_name: str, limit: int = 100) -> Dict[str, Any]:
    """
    Get a preview of cleaned data for a specific table.
    
    Args:
        db: Database session
        table_name: Name of the table to preview
        limit: Maximum number of rows to return
    
    Returns:
        Dict containing cleaned data preview and metadata
    """
    
    cleaners = {
        "plants": _clean_and_normalize_plants,
        "production_capacity_cost": _clean_and_normalize_production_capacity,
        "transport_routes_modes": _clean_and_normalize_transport_routes,
        "demand_forecast": _clean_and_normalize_demand_forecast,
        "initial_inventory": _clean_and_normalize_initial_inventory,
        "safety_stock_policy": _clean_and_normalize_safety_stock_policy
    }
    
    if table_name not in cleaners:
        raise ValueError(f"Unknown table: {table_name}")
    
    try:
        df = cleaners[table_name](db)
        
        # Apply limit
        preview_df = df.head(limit)
        
        return {
            "table_name": table_name,
            "data": preview_df.to_dict(orient="records"),
            "columns": list(df.columns),
            "total_rows": len(df),
            "preview_rows": len(preview_df),
            "data_types": df.dtypes.astype(str).to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
            "cleaned_at": pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting clean data preview for {table_name}: {e}")
        raise DataValidationError(f"Failed to get clean data preview: {str(e)}")


def get_all_clean_data_previews(db: Session, limit: int = 50) -> Dict[str, Any]:
    """Get previews of all cleaned data tables."""
    
    table_names = [
        "plants",
        "production_capacity_cost", 
        "transport_routes_modes",
        "demand_forecast",
        "initial_inventory",
        "safety_stock_policy"
    ]
    
    previews = {}
    for table_name in table_names:
        try:
            previews[table_name] = get_clean_data_preview(db, table_name, limit)
        except Exception as e:
            logger.error(f"Error getting preview for {table_name}: {e}")
            previews[table_name] = {
                "table_name": table_name,
                "error": str(e),
                "data": [],
                "columns": [],
                "total_rows": 0,
                "preview_rows": 0
            }
    
    return {
        "previews": previews,
        "generated_at": pd.Timestamp.now().isoformat()
    }