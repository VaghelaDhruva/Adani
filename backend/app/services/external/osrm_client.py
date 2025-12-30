"""
OSRM Client with Retry and Exponential Backoff - PHASE 2 ROUTING FIX

This module provides a robust OSRM client that:
1. Uses REAL coordinates (not hardcoded 0,0)
2. Implements retry with exponential backoff
3. Has proper timeout handling
4. Provides structured error logging
5. Handles API failures gracefully

NO MORE SILENT FAILURES!
"""

import httpx
import asyncio
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from app.core.config import get_settings
from app.utils.exceptions import ExternalAPIError

settings = get_settings()
logger = logging.getLogger(__name__)


async def get_route_osrm(origin_coords: Tuple[float, float], dest_coords: Tuple[float, float]) -> Optional[Dict[str, Any]]:
    """
    Query OSRM for route distance and duration with retry and exponential backoff.
    
    Args:
        origin_coords: (latitude, longitude) tuple for origin
        dest_coords: (latitude, longitude) tuple for destination
        
    Returns:
        Dict with distance_m, duration_s, provider, or None if all retries failed
        
    Raises:
        ExternalAPIError: If there's a configuration or validation error
    """
    # Validate coordinates
    if not _validate_coordinates(origin_coords[0], origin_coords[1]):
        raise ExternalAPIError(f"Invalid origin coordinates: {origin_coords}")
    
    if not _validate_coordinates(dest_coords[0], dest_coords[1]):
        raise ExternalAPIError(f"Invalid destination coordinates: {dest_coords}")
    
    # OSRM expects longitude,latitude format (not latitude,longitude!)
    origin_str = f"{origin_coords[1]},{origin_coords[0]}"  # lng,lat
    dest_str = f"{dest_coords[1]},{dest_coords[0]}"        # lng,lat
    
    url = f"{settings.OSRM_BASE_URL}/route/v1/driving/{origin_str};{dest_str}"
    params = {
        "overview": "false",
        "geometries": "geojson",
        "steps": "false"
    }
    
    # Retry with exponential backoff
    for attempt in range(settings.ROUTING_MAX_RETRIES):
        try:
            logger.debug(f"OSRM attempt {attempt + 1}/{settings.ROUTING_MAX_RETRIES}: {url}")
            
            async with httpx.AsyncClient() as client:
                start_time = datetime.now()
                
                response = await client.get(
                    url, 
                    params=params, 
                    timeout=settings.ROUTING_TIMEOUT_SECONDS
                )
                
                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                response.raise_for_status()
                data = response.json()
                
                # Check OSRM response structure
                if data.get("code") != "Ok":
                    error_msg = data.get("message", "Unknown OSRM error")
                    logger.warning(f"OSRM API error: {error_msg}")
                    
                    # Don't retry for certain errors
                    if data.get("code") in ["NoRoute", "InvalidInput"]:
                        logger.error(f"OSRM permanent error for route {origin_coords} -> {dest_coords}: {error_msg}")
                        return None
                    
                    # Retry for other errors
                    raise ExternalAPIError(f"OSRM API error: {error_msg}")
                
                routes = data.get("routes", [])
                if not routes:
                    logger.warning(f"OSRM returned no routes for {origin_coords} -> {dest_coords}")
                    return None
                
                route = routes[0]
                distance_m = route.get("distance", 0)
                duration_s = route.get("duration", 0)
                
                logger.info(f"OSRM success: {distance_m/1000:.1f}km, {duration_s/60:.1f}min ({elapsed_ms:.0f}ms)")
                
                return {
                    "distance_m": distance_m,
                    "duration_s": duration_s,
                    "provider": "osrm",
                    "response_time_ms": elapsed_ms,
                    "attempt": attempt + 1
                }
                
        except httpx.TimeoutException:
            logger.warning(f"OSRM timeout on attempt {attempt + 1}/{settings.ROUTING_MAX_RETRIES}")
            if attempt == settings.ROUTING_MAX_RETRIES - 1:
                logger.error(f"OSRM timeout after {settings.ROUTING_MAX_RETRIES} attempts")
                return None
                
        except httpx.HTTPStatusError as e:
            logger.warning(f"OSRM HTTP error {e.response.status_code} on attempt {attempt + 1}/{settings.ROUTING_MAX_RETRIES}")
            
            # Don't retry for client errors (4xx)
            if 400 <= e.response.status_code < 500:
                logger.error(f"OSRM client error {e.response.status_code}: {e.response.text}")
                return None
            
            # Retry for server errors (5xx)
            if attempt == settings.ROUTING_MAX_RETRIES - 1:
                logger.error(f"OSRM server error after {settings.ROUTING_MAX_RETRIES} attempts: {e}")
                return None
                
        except httpx.RequestError as e:
            logger.warning(f"OSRM request error on attempt {attempt + 1}/{settings.ROUTING_MAX_RETRIES}: {e}")
            if attempt == settings.ROUTING_MAX_RETRIES - 1:
                logger.error(f"OSRM request failed after {settings.ROUTING_MAX_RETRIES} attempts: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Unexpected OSRM error on attempt {attempt + 1}/{settings.ROUTING_MAX_RETRIES}: {e}")
            if attempt == settings.ROUTING_MAX_RETRIES - 1:
                return None
        
        # Exponential backoff delay
        if attempt < settings.ROUTING_MAX_RETRIES - 1:
            delay = settings.ROUTING_RETRY_DELAY * (settings.ROUTING_RETRY_BACKOFF ** attempt)
            logger.debug(f"OSRM retry delay: {delay:.1f}s")
            await asyncio.sleep(delay)
    
    logger.error(f"OSRM failed after {settings.ROUTING_MAX_RETRIES} attempts")
    return None


def _validate_coordinates(lat: float, lng: float) -> bool:
    """
    Validate coordinate ranges.
    
    Args:
        lat: Latitude
        lng: Longitude
        
    Returns:
        True if valid, False otherwise
    """
    return (-90 <= lat <= 90) and (-180 <= lng <= 180)


async def test_osrm_connectivity() -> Dict[str, Any]:
    """
    Test OSRM connectivity with a known route.
    
    Returns:
        Dict with test results
    """
    # Test route: Mumbai to Delhi
    mumbai = (19.0760, 72.8777)
    delhi = (28.7041, 77.1025)
    
    try:
        start_time = datetime.now()
        result = await get_route_osrm(mumbai, delhi)
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        if result:
            return {
                "status": "success",
                "distance_km": result["distance_m"] / 1000,
                "duration_minutes": result["duration_s"] / 60,
                "response_time_ms": elapsed_ms,
                "provider": result["provider"]
            }
        else:
            return {
                "status": "failed",
                "error": "No route returned",
                "response_time_ms": elapsed_ms
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "response_time_ms": 0
        }
