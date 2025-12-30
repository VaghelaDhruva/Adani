"""
Routing Cache Service with Real Coordinates - PHASE 2 ROUTING FIX

This service provides intelligent routing with:
1. REAL coordinates from plant_master table (NO MORE 0,0!)
2. Robust retry with exponential backoff
3. Intelligent fallback between OSRM and ORS
4. Comprehensive caching with last-known-good values
5. Structured error logging instead of silent failures

CRITICAL IMPROVEMENTS:
- Plant lat/lng comes from plant_master table
- OSRM client uses real coordinates
- Retry with exponential backoff implemented
- Timeout handling implemented
- Cache successful lookups in transport_lookup
- If OSRM + ORS both fail → log warning & use last known cached value
- Structured error logs instead of silent None returns
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.transport_lookup import TransportLookup
from app.db.models.plant_master import PlantMaster
from app.services.external.osrm_client import get_route_osrm
from app.services.external.ors_client import get_route_ors
from app.services.coordinate_resolver import get_route_coordinates
from app.core.config import get_settings
from app.utils.exceptions import DataValidationError, ExternalAPIError

settings = get_settings()
logger = logging.getLogger(__name__)


async def get_route_with_cache(
    db: Session,
    origin_plant_id: str,
    destination_node_id: str,
    transport_mode: str = "driving",
) -> Optional[Dict[str, Any]]:
    """
    Get route distance and duration with intelligent caching and fallback.
    
    PHASE 2 IMPROVEMENTS:
    1. Uses REAL coordinates from plant_master table
    2. Implements retry with exponential backoff
    3. Intelligent fallback between OSRM and ORS
    4. Uses last-known-good cached values if APIs fail
    5. Comprehensive error logging
    
    Args:
        db: Database session
        origin_plant_id: Plant ID for origin
        destination_node_id: Node ID for destination
        transport_mode: Transport mode (default: driving)
        
    Returns:
        Dict with distance_km, duration_minutes, source, or None if all methods fail
    """
    logger.info(f"Getting route: {origin_plant_id} -> {destination_node_id} ({transport_mode})")
    
    # 1) Check cache first
    cached = (
        db.query(TransportLookup)
        .filter(
            TransportLookup.origin_plant_id == origin_plant_id,
            TransportLookup.destination_node_id == destination_node_id,
            TransportLookup.transport_mode == transport_mode,
        )
        .first()
    )
    
    if cached:
        # Check if cache is recent (within 30 days) - use it directly
        if cached.created_at and (datetime.utcnow() - cached.created_at).days < 30:
            logger.info(f"Using fresh cached route: {cached.distance_km:.1f}km, {cached.duration_minutes:.1f}min ({cached.source})")
            return {
                "distance_km": cached.distance_km,
                "duration_minutes": cached.duration_minutes,
                "source": cached.source,
                "cached": True,
                "cache_age_days": (datetime.utcnow() - cached.created_at).days
            }
        else:
            logger.info(f"Found stale cached route ({(datetime.utcnow() - cached.created_at).days} days old), will try to refresh")
    
    # 2) Not cached or stale: resolve coordinates and fetch from external APIs
    try:
        # PHASE 2 FIX: Get REAL coordinates from plant_master table
        origin_coords, dest_coords = get_route_coordinates(db, origin_plant_id, destination_node_id)
        logger.info(f"Resolved coordinates: {origin_plant_id} {origin_coords} -> {destination_node_id} {dest_coords}")
        
    except DataValidationError as e:
        logger.error(f"Failed to resolve coordinates for route {origin_plant_id} -> {destination_node_id}: {e}")
        
        # If we have stale cached data, use it as fallback
        if cached:
            logger.warning(f"Using stale cached route due to coordinate resolution failure: {cached.distance_km:.1f}km")
            return {
                "distance_km": cached.distance_km,
                "duration_minutes": cached.duration_minutes,
                "source": f"{cached.source}_stale",
                "cached": True,
                "cache_age_days": (datetime.utcnow() - cached.created_at).days,
                "warning": "Using stale cache due to coordinate resolution failure"
            }
        
        return None
    
    # 3) Try external APIs with intelligent fallback
    result = None
    provider = None
    api_errors = []
    
    # Try ORS first if API key is configured (usually more reliable)
    if settings.ORS_API_KEY and settings.ORS_BASE_URL:
        try:
            logger.debug("Trying ORS API...")
            result = await get_route_ors(origin_coords, dest_coords)
            if result:
                provider = "ORS"
                logger.info(f"ORS success: {result['distance_m']/1000:.1f}km, {result['duration_s']/60:.1f}min")
        except Exception as e:
            api_errors.append(f"ORS failed: {e}")
            logger.warning(f"ORS API failed: {e}")
    
    # Fallback to OSRM if ORS failed or not configured
    if not result:
        try:
            logger.debug("Trying OSRM API...")
            result = await get_route_osrm(origin_coords, dest_coords)
            if result:
                provider = "OSRM"
                logger.info(f"OSRM success: {result['distance_m']/1000:.1f}km, {result['duration_s']/60:.1f}min")
        except Exception as e:
            api_errors.append(f"OSRM failed: {e}")
            logger.warning(f"OSRM API failed: {e}")
    
    # 4) Handle API failures
    if not result:
        logger.error(f"All routing APIs failed for {origin_plant_id} -> {destination_node_id}: {'; '.join(api_errors)}")
        
        # PHASE 2 FIX: Use last known cached value if available
        if cached:
            logger.warning(f"Using last known cached route due to API failures: {cached.distance_km:.1f}km ({cached.source})")
            return {
                "distance_km": cached.distance_km,
                "duration_minutes": cached.duration_minutes,
                "source": f"{cached.source}_fallback",
                "cached": True,
                "cache_age_days": (datetime.utcnow() - cached.created_at).days,
                "warning": f"Using cached fallback due to API failures: {'; '.join(api_errors)}"
            }
        
        # No cached data available - complete failure
        logger.error(f"No cached fallback available for route {origin_plant_id} -> {destination_node_id}")
        return None
    
    # 5) Store successful result in cache
    distance_km = result.get("distance_m", 0) / 1000.0
    duration_minutes = result.get("duration_s", 0) / 60.0
    
    try:
        # Update existing cache entry or create new one
        if cached:
            cached.distance_km = distance_km
            cached.duration_minutes = duration_minutes
            cached.source = provider
            cached.updated_at = datetime.utcnow()
            logger.info(f"Updated cached route: {distance_km:.1f}km, {duration_minutes:.1f}min ({provider})")
        else:
            cache_entry = TransportLookup(
                origin_plant_id=origin_plant_id,
                destination_node_id=destination_node_id,
                transport_mode=transport_mode,
                distance_km=distance_km,
                duration_minutes=duration_minutes,
                source=provider,
            )
            db.add(cache_entry)
            logger.info(f"Cached new route: {distance_km:.1f}km, {duration_minutes:.1f}min ({provider})")
        
        db.commit()
        
    except IntegrityError:
        # Duplicate entry - safe to ignore for idempotency
        db.rollback()
        logger.debug("Duplicate cache entry - ignoring")
    except SQLAlchemyError as e:
        # Database error - log but don't fail the request
        db.rollback()
        logger.error(f"Failed to cache route result: {e}")
    
    # 6) Return successful result
    return {
        "distance_km": distance_km,
        "duration_minutes": duration_minutes,
        "source": provider,
        "cached": False,
        "response_time_ms": result.get("response_time_ms", 0),
        "attempt": result.get("attempt", 1)
    }


async def test_routing_connectivity(db: Session) -> Dict[str, Any]:
    """
    Test routing connectivity and coordinate resolution.
    
    Args:
        db: Database session
        
    Returns:
        Dict with test results
    """
    test_results = {
        "timestamp": datetime.utcnow().isoformat(),
        "coordinate_resolution": {},
        "osrm_test": {},
        "ors_test": {},
        "cache_test": {}
    }
    
    # Test coordinate resolution
    try:
        from app.services.coordinate_resolver import CoordinateResolver
        resolver = CoordinateResolver(db)
        
        # Try to resolve a known plant
        plants = db.query(PlantMaster).limit(2).all()
        if len(plants) >= 2:
            plant1, plant2 = plants[0], plants[1]
            coords1 = resolver.get_plant_coordinates(plant1.plant_id)
            coords2 = resolver.get_plant_coordinates(plant2.plant_id)
            
            test_results["coordinate_resolution"] = {
                "status": "success",
                "plant1": {"id": plant1.plant_id, "coords": coords1},
                "plant2": {"id": plant2.plant_id, "coords": coords2}
            }
        else:
            test_results["coordinate_resolution"] = {
                "status": "failed",
                "error": "Not enough plants in database for testing"
            }
            
    except Exception as e:
        test_results["coordinate_resolution"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Test OSRM connectivity
    try:
        from app.services.external.osrm_client import test_osrm_connectivity
        test_results["osrm_test"] = await test_osrm_connectivity()
    except Exception as e:
        test_results["osrm_test"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Test ORS connectivity
    try:
        from app.services.external.ors_client import test_ors_connectivity
        test_results["ors_test"] = await test_ors_connectivity()
    except Exception as e:
        test_results["ors_test"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Test cache functionality
    try:
        cache_count = db.query(TransportLookup).count()
        test_results["cache_test"] = {
            "status": "success",
            "cached_routes": cache_count
        }
    except Exception as e:
        test_results["cache_test"] = {
            "status": "error",
            "error": str(e)
        }
    
    return test_results


def clear_routing_cache(db: Session, older_than_days: int = 30) -> Dict[str, Any]:
    """
    Clear old routing cache entries.
    
    Args:
        db: Database session
        older_than_days: Clear entries older than this many days
        
    Returns:
        Dict with cleanup results
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        
        deleted_count = db.query(TransportLookup).filter(
            TransportLookup.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleared {deleted_count} routing cache entries older than {older_than_days} days")
        
        return {
            "status": "success",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to clear routing cache: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
