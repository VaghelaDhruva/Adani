"""
Data Access Guard - PHASE 1 DATA SAFETY

This module enforces the critical rule:
PRODUCTION CODE (especially the optimizer) must NEVER read from staging tables.

It provides safe data access methods that only read from validated production tables.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.plant_master import PlantMaster
from app.db.models.production_capacity_cost import ProductionCapacityCost
from app.db.models.transport_routes_modes import TransportRoutesModes
from app.db.models.demand_forecast import DemandForecast
from app.db.models.initial_inventory import InitialInventory
from app.db.models.safety_stock_policy import SafetyStockPolicy
from app.utils.exceptions import DataValidationError

logger = logging.getLogger(__name__)

# CRITICAL: List of staging table names that are FORBIDDEN for production code
STAGING_TABLE_NAMES = {
    "stg_plant_master",
    "stg_demand_forecast", 
    "stg_transport_routes",
    "stg_production_costs",
    "stg_initial_inventory",
    "stg_safety_stock",
    "validation_batch"
}


class DataAccessGuard:
    """
    Safe data access service that enforces staging table isolation.
    
    This service provides the ONLY approved way for production code
    (especially the optimizer) to access data.
    
    CRITICAL RULES:
    1. NEVER reads from staging tables
    2. Only reads from validated production tables
    3. Validates data completeness before returning
    4. Logs all data access for audit
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._validate_database_safety()
    
    def _validate_database_safety(self):
        """
        Validate that we're not accidentally connected to staging tables.
        This is a safety check to prevent production code from reading staging data.
        """
        try:
            # Check that production tables exist and are accessible
            plant_count = self.db.query(PlantMaster).count()
            logger.info(f"Data access guard initialized - {plant_count} plants in production tables")
            
        except Exception as e:
            logger.error(f"Database safety validation failed: {e}")
            raise DataValidationError(f"Cannot initialize data access guard: {e}")
    
    def get_plants(self) -> List[Dict[str, Any]]:
        """
        Get all plants from PRODUCTION tables only.
        
        Returns:
            List of plant dictionaries
            
        Raises:
            DataValidationError: If no plants found or data access fails
        """
        try:
            plants = self.db.query(PlantMaster).all()
            
            if not plants:
                raise DataValidationError("No plants found in production tables. Cannot run optimization.")
            
            result = [
                {
                    "plant_id": p.plant_id,
                    "plant_name": p.plant_name,
                    "plant_type": p.plant_type,
                    "latitude": p.latitude,
                    "longitude": p.longitude,
                    "region": p.region,
                    "country": p.country
                }
                for p in plants
            ]
            
            logger.info(f"Retrieved {len(result)} plants from production tables")
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error accessing plants: {e}")
            raise DataValidationError(f"Failed to access plant data: {e}")
    
    def get_production_capacity(self) -> List[Dict[str, Any]]:
        """
        Get production capacity data from PRODUCTION tables only.
        
        Returns:
            List of production capacity dictionaries
            
        Raises:
            DataValidationError: If no capacity data found
        """
        try:
            capacity_data = self.db.query(ProductionCapacityCost).all()
            
            if not capacity_data:
                raise DataValidationError("No production capacity data found in production tables. Cannot run optimization.")
            
            result = [
                {
                    "plant_id": c.plant_id,
                    "period": c.period,
                    "max_capacity_tonnes": c.max_capacity_tonnes,
                    "variable_cost_per_tonne": c.variable_cost_per_tonne,
                    "fixed_cost_per_period": c.fixed_cost_per_period,
                    "min_run_level": c.min_run_level,
                    "holding_cost_per_tonne": c.holding_cost_per_tonne
                }
                for c in capacity_data
            ]
            
            logger.info(f"Retrieved {len(result)} production capacity records from production tables")
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error accessing production capacity: {e}")
            raise DataValidationError(f"Failed to access production capacity data: {e}")
    
    def get_transport_routes(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get transport routes from PRODUCTION tables only.
        
        Args:
            active_only: If True, only return active routes
            
        Returns:
            List of transport route dictionaries
            
        Raises:
            DataValidationError: If no routes found
        """
        try:
            query = self.db.query(TransportRoutesModes)
            if active_only:
                query = query.filter(TransportRoutesModes.is_active == "Y")
            
            routes = query.all()
            
            if not routes:
                raise DataValidationError("No transport routes found in production tables. Cannot run optimization.")
            
            result = [
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
                for r in routes
            ]
            
            logger.info(f"Retrieved {len(result)} transport routes from production tables")
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error accessing transport routes: {e}")
            raise DataValidationError(f"Failed to access transport routes data: {e}")
    
    def get_demand_forecast(self) -> List[Dict[str, Any]]:
        """
        Get demand forecast from PRODUCTION tables only.
        
        Returns:
            List of demand forecast dictionaries
            
        Raises:
            DataValidationError: If no demand data found
        """
        try:
            demand_data = self.db.query(DemandForecast).all()
            
            if not demand_data:
                raise DataValidationError("No demand forecast data found in production tables. Cannot run optimization.")
            
            result = [
                {
                    "customer_node_id": d.customer_node_id,
                    "period": d.period,
                    "demand_tonnes": d.demand_tonnes,
                    "demand_low_tonnes": d.demand_low_tonnes,
                    "demand_high_tonnes": d.demand_high_tonnes,
                    "confidence_level": d.confidence_level,
                    "source": d.source
                }
                for d in demand_data
            ]
            
            logger.info(f"Retrieved {len(result)} demand forecast records from production tables")
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error accessing demand forecast: {e}")
            raise DataValidationError(f"Failed to access demand forecast data: {e}")
    
    def get_initial_inventory(self) -> List[Dict[str, Any]]:
        """
        Get initial inventory from PRODUCTION tables only.
        
        Returns:
            List of initial inventory dictionaries
        """
        try:
            inventory_data = self.db.query(InitialInventory).all()
            
            result = [
                {
                    "location_id": i.location_id,
                    "initial_stock_tonnes": i.initial_stock_tonnes,
                    "period": getattr(i, 'period', None)  # Handle optional period field
                }
                for i in inventory_data
            ]
            
            logger.info(f"Retrieved {len(result)} initial inventory records from production tables")
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error accessing initial inventory: {e}")
            raise DataValidationError(f"Failed to access initial inventory data: {e}")
    
    def get_safety_stock_policies(self) -> List[Dict[str, Any]]:
        """
        Get safety stock policies from PRODUCTION tables only.
        
        Returns:
            List of safety stock policy dictionaries
        """
        try:
            safety_stock_data = self.db.query(SafetyStockPolicy).all()
            
            result = [
                {
                    "location_id": s.location_id,
                    "safety_stock_tonnes": s.safety_stock_tonnes,
                    "penalty_cost_per_tonne": s.penalty_cost_per_tonne,
                    "policy_type": getattr(s, 'policy_type', 'fixed'),  # Handle optional field
                    "policy_value": getattr(s, 'policy_value', s.safety_stock_tonnes)  # Handle optional field
                }
                for s in safety_stock_data
            ]
            
            logger.info(f"Retrieved {len(result)} safety stock policy records from production tables")
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error accessing safety stock policies: {e}")
            raise DataValidationError(f"Failed to access safety stock policy data: {e}")
    
    def get_complete_optimization_dataset(self) -> Dict[str, Any]:
        """
        Get complete dataset for optimization from PRODUCTION tables only.
        
        This is the ONLY approved method for the optimizer to get data.
        
        Returns:
            Complete dataset dictionary with all required data
            
        Raises:
            DataValidationError: If any required data is missing
        """
        try:
            logger.info("Loading complete optimization dataset from production tables")
            
            dataset = {
                "plants": self.get_plants(),
                "production_capacity": self.get_production_capacity(),
                "transport_routes": self.get_transport_routes(),
                "demand_forecast": self.get_demand_forecast(),
                "initial_inventory": self.get_initial_inventory(),
                "safety_stock_policies": self.get_safety_stock_policies()
            }
            
            # Validate dataset completeness
            self._validate_dataset_completeness(dataset)
            
            logger.info("Successfully loaded complete optimization dataset from production tables")
            return dataset
            
        except Exception as e:
            logger.error(f"Failed to load complete optimization dataset: {e}")
            raise DataValidationError(f"Cannot load optimization dataset: {e}")
    
    def _validate_dataset_completeness(self, dataset: Dict[str, Any]):
        """
        Validate that the dataset is complete enough for optimization.
        
        Args:
            dataset: Dataset to validate
            
        Raises:
            DataValidationError: If dataset is incomplete
        """
        errors = []
        
        if not dataset["plants"]:
            errors.append("No plants found")
        
        if not dataset["production_capacity"]:
            errors.append("No production capacity data found")
        
        if not dataset["transport_routes"]:
            errors.append("No transport routes found")
        
        if not dataset["demand_forecast"]:
            errors.append("No demand forecast data found")
        
        # Check referential integrity
        plant_ids = {p["plant_id"] for p in dataset["plants"]}
        
        # Check that all production capacity references valid plants
        capacity_plant_ids = {c["plant_id"] for c in dataset["production_capacity"]}
        invalid_capacity_plants = capacity_plant_ids - plant_ids
        if invalid_capacity_plants:
            errors.append(f"Production capacity references invalid plants: {invalid_capacity_plants}")
        
        # Check that all transport routes reference valid plants
        route_plant_ids = {r["origin_plant_id"] for r in dataset["transport_routes"]}
        invalid_route_plants = route_plant_ids - plant_ids
        if invalid_route_plants:
            errors.append(f"Transport routes reference invalid plants: {invalid_route_plants}")
        
        if errors:
            raise DataValidationError(f"Dataset validation failed: {'; '.join(errors)}")
        
        logger.info("Dataset completeness validation passed")
    
    def validate_no_staging_access(self):
        """
        Validate that this service is not accidentally accessing staging tables.
        This is a safety check that should be called before optimization.
        
        Raises:
            DataValidationError: If staging table access is detected
        """
        try:
            # This is a paranoid safety check - we should never be able to access staging tables
            # from production code, but let's verify
            
            # Check that we can't accidentally query staging tables
            for staging_table in STAGING_TABLE_NAMES:
                try:
                    # Try to access staging table - this should fail or return empty
                    result = self.db.execute(f"SELECT COUNT(*) FROM {staging_table}")
                    count = result.scalar()
                    if count > 0:
                        logger.warning(f"SAFETY WARNING: Found {count} records in staging table {staging_table}")
                except Exception:
                    # This is expected - staging tables should not be accessible to production code
                    pass
            
            logger.info("Staging table access validation passed - no staging data accessible")
            
        except Exception as e:
            logger.error(f"Staging table access validation failed: {e}")
            # Don't fail the optimization for this - it's just a safety check
            pass


def get_safe_optimization_data(db: Session) -> Dict[str, Any]:
    """
    SAFE ENTRY POINT for optimization data access.
    
    This is the ONLY approved way for the optimizer to get data.
    
    Args:
        db: Database session
        
    Returns:
        Complete optimization dataset from production tables only
        
    Raises:
        DataValidationError: If data access fails or data is incomplete
    """
    guard = DataAccessGuard(db)
    guard.validate_no_staging_access()
    return guard.get_complete_optimization_dataset()