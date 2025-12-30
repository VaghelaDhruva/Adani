"""
Coordinate Resolver Service - PHASE 2 ROUTING FIX

This service resolves plant_id and node_id to actual coordinates.
NO MORE HARDCODED (0,0) COORDINATES!

It provides the real lat/lng data needed for OSRM and ORS routing APIs.
"""

import logging
from typing import Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.plant_master import PlantMaster
from app.utils.exceptions import DataValidationError

logger = logging.getLogger(__name__)

# Cache for coordinate lookups to avoid repeated DB queries
_coordinate_cache: Dict[str, Tuple[float, float]] = {}


class CoordinateResolver:
    """
    Service to resolve plant IDs and node IDs to real coordinates.
    
    This replaces the hardcoded (0,0) coordinates with actual lat/lng data
    from the plant_master table and future customer/node tables.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_plant_coordinates(self, plant_id: str) -> Tuple[float, float]:
        """
        Get real coordinates for a plant ID.
        
        Args:
            plant_id: Plant identifier
            
        Returns:
            Tuple of (latitude, longitude)
            
        Raises:
            DataValidationError: If plant not found or coordinates missing
        """
        # Check cache first
        cache_key = f"plant_{plant_id}"
        if cache_key in _coordinate_cache:
            return _coordinate_cache[cache_key]
        
        try:
            plant = self.db.query(PlantMaster).filter(PlantMaster.plant_id == plant_id).first()
            
            if not plant:
                raise DataValidationError(f"Plant {plant_id} not found")
            
            if plant.latitude is None or plant.longitude is None:
                raise DataValidationError(f"Plant {plant_id} has missing coordinates (lat: {plant.latitude}, lng: {plant.longitude})")
            
            # Validate coordinate ranges
            if not (-90 <= plant.latitude <= 90):
                raise DataValidationError(f"Plant {plant_id} has invalid latitude: {plant.latitude}")
            
            if not (-180 <= plant.longitude <= 180):
                raise DataValidationError(f"Plant {plant_id} has invalid longitude: {plant.longitude}")
            
            coordinates = (plant.latitude, plant.longitude)
            
            # Cache the result
            _coordinate_cache[cache_key] = coordinates
            
            logger.debug(f"Resolved plant {plant_id} to coordinates {coordinates}")
            return coordinates
            
        except SQLAlchemyError as e:
            logger.error(f"Database error resolving coordinates for plant {plant_id}: {e}")
            raise DataValidationError(f"Failed to resolve coordinates for plant {plant_id}: {e}")
    
    def get_node_coordinates(self, node_id: str) -> Tuple[float, float]:
        """
        Get coordinates for a destination node (could be plant or customer).
        
        Args:
            node_id: Node identifier
            
        Returns:
            Tuple of (latitude, longitude)
            
        Raises:
            DataValidationError: If node not found or coordinates missing
        """
        # Check cache first
        cache_key = f"node_{node_id}"
        if cache_key in _coordinate_cache:
            return _coordinate_cache[cache_key]
        
        try:
            # First try to find as a plant
            plant = self.db.query(PlantMaster).filter(PlantMaster.plant_id == node_id).first()
            
            if plant and plant.latitude is not None and plant.longitude is not None:
                coordinates = (plant.latitude, plant.longitude)
                _coordinate_cache[cache_key] = coordinates
                logger.debug(f"Resolved node {node_id} as plant to coordinates {coordinates}")
                return coordinates
            
            # TODO: In future, add customer/node table lookup here
            # For now, if it's not a plant, we need to handle it
            
            # If node_id looks like a customer ID, use predefined customer locations
            # This is a temporary solution until customer coordinate table is implemented
            customer_coordinates = self._get_customer_coordinates(node_id)
            if customer_coordinates:
                _coordinate_cache[cache_key] = customer_coordinates
                logger.debug(f"Resolved node {node_id} as customer to coordinates {customer_coordinates}")
                return customer_coordinates
            
            raise DataValidationError(f"Node {node_id} not found in plants or customer locations")
            
        except SQLAlchemyError as e:
            logger.error(f"Database error resolving coordinates for node {node_id}: {e}")
            raise DataValidationError(f"Failed to resolve coordinates for node {node_id}: {e}")
    
    def _get_customer_coordinates(self, customer_id: str) -> Optional[Tuple[float, float]]:
        """
        Get predefined customer coordinates.
        
        This is a temporary solution until we have a proper customer table.
        In production, this should be replaced with database lookups.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        # Predefined customer locations (major Indian cities)
        customer_locations = {
            "CUST_001": (19.0760, 72.8777),  # Mumbai
            "CUST_002": (28.7041, 77.1025),  # Delhi
            "CUST_003": (13.0827, 80.2707),  # Chennai
            "CUST_004": (12.9716, 77.5946),  # Bangalore
            "CUST_005": (22.5726, 88.3639),  # Kolkata
            "CUST_006": (23.0225, 72.5714),  # Ahmedabad
            "CUST_007": (18.5204, 73.8567),  # Pune
            "CUST_008": (17.3850, 78.4867),  # Hyderabad
            "CUST_009": (26.9124, 75.7873),  # Jaipur
            "CUST_010": (21.1458, 79.0882),  # Nagpur
        }
        
        return customer_locations.get(customer_id)
    
    def get_route_coordinates(self, origin_plant_id: str, destination_node_id: str) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Get coordinates for both origin and destination.
        
        Args:
            origin_plant_id: Origin plant ID
            destination_node_id: Destination node ID
            
        Returns:
            Tuple of ((origin_lat, origin_lng), (dest_lat, dest_lng))
            
        Raises:
            DataValidationError: If either coordinate cannot be resolved
        """
        try:
            origin_coords = self.get_plant_coordinates(origin_plant_id)
            dest_coords = self.get_node_coordinates(destination_node_id)
            
            logger.info(f"Resolved route coordinates: {origin_plant_id} {origin_coords} -> {destination_node_id} {dest_coords}")
            return origin_coords, dest_coords
            
        except Exception as e:
            logger.error(f"Failed to resolve route coordinates for {origin_plant_id} -> {destination_node_id}: {e}")
            raise DataValidationError(f"Cannot resolve route coordinates: {e}")
    
    def validate_coordinates(self, lat: float, lng: float) -> bool:
        """
        Validate that coordinates are within valid ranges.
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            True if valid, False otherwise
        """
        return (-90 <= lat <= 90) and (-180 <= lng <= 180)
    
    def clear_cache(self):
        """Clear the coordinate cache. Useful for testing or when data changes."""
        global _coordinate_cache
        _coordinate_cache.clear()
        logger.info("Coordinate cache cleared")


def get_route_coordinates(db: Session, origin_plant_id: str, destination_node_id: str) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    Convenience function to get route coordinates.
    
    Args:
        db: Database session
        origin_plant_id: Origin plant ID
        destination_node_id: Destination node ID
        
    Returns:
        Tuple of ((origin_lat, origin_lng), (dest_lat, dest_lng))
        
    Raises:
        DataValidationError: If coordinates cannot be resolved
    """
    resolver = CoordinateResolver(db)
    return resolver.get_route_coordinates(origin_plant_id, destination_node_id)