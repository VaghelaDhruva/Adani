"""
OpenRouteService Client with Retry and Exponential Backoff - PHASE 2 ROUTING FIX

This module provides a robust ORS client that:
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


async def get_route_ors(origin_coords: Tuple[float, float], dest_coords: Tuple[float, float]) -> Optional[Dict[str, Any]]:
    """
    Query OpenRouteService for route distance and duration with retry and exponential backoff.
    
    Args:
        origin_coords: (latitude, longitude) tuple for origin
        dest_coords: (latitude, longitude) tuple for destination
        
    Returns:
        Dict with distance_m, duration_s, provider, or None if all retries failed
        
    Raises:
        ExternalAPIError: If there's a configuration or validation error
    """
    if not settings.ORS_API_KEY:
        raise ExternalAPIError("ORS_API_KEY not configured")
    
    # Validate coordinates
    if not _validate_coordinates(origin_coords[0], origin_coords[1]):
        raise ExternalAPIError(f"Invalid origin coordinates: {origin_coords}")
    
    if not _validate_coordinates(dest_coords[0], dest_coords[1]):
        raise ExternalAPIError(f"Invalid destination coordinates: {dest_coords}")
    
    url = f"{settings.ORS_BASE_URL}/v2/directions/driving-car"
    headers = {
        "Authorization": f"Bearer {settings.ORS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # ORS expects longitude,latitude format
    payload = {
        "coordinates": [
            [dest_coords[1], dest_coords[0]],    # destination: [lng, lat]
            [origin_coords[1], origin_coords[0]]  # origin: [lng, lat]
        ],
        "format": "json",
        "instructions": False,
        "geometry": False
    }
    
    # Retry with exponential backoff
    for attempt in range(settings.ROUTING_MAX_RETRIES):
        try:
            logger.debug(f"ORS attempt {attempt + 1}/{settings.ROUTING_MAX_RETRIES}: {url}")
            
            async with httpx.AsyncClient() as client:
                start_time = datetime.now()
                
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=settings.ROUTING_TIMEOUT_SECONDS
                )
                
                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                response.raise_for_status()
                data = response.json()
                
                # Check ORS response structure
                routes = data.get("routes", [])
                if not routes:
                    logger.warning(f"ORS returned no routes for {origin_coords} -> {dest_coords}")
                    return None
                
                route = routes[0]
                summary = route.get("summary", {})
                distance_m = summary.get("distance", 0)
                duration_s = summary.get("duration", 0)
                
                logger.info(f"ORS success: {distance_m/1000:.1f}km, {duration_s/60:.1f}min ({elapsed_ms:.0f}ms)")
                
                return {
                    "distance_m": distance_m,
                    "duration_s": duration_s,
                    "provider": "ors",
                    "response_time_ms": elapsed_ms,
                    "attempt": attempt + 1
                }
                
        except httpx.TimeoutException:
            logger.warning(f"ORS timeout on attempt {attempt + 1}/{settings.ROUTING_MAX_RETRIES}")
            if attempt == settings.ROUTING_MAX_RETRIES - 1:
                logger.error(f"ORS timeout after {settings.ROUTING_MAX_RETRIES} attempts")
                return None
                
        except httpx.HTTPStatusError as e:
            logger.warning(f"ORS HTTP error {e.response.status_code} on attempt {attempt + 1}/{settings.ROUTING_MAX_RETRIES}")
            
            # Handle specific ORS error codes
            if e.response.status_code == 401:
                logger.error("ORS authentication failed - check API key")
                return None
            elif e.response.status_code == 403:
                logger.error("ORS access forbidden - check API key permissions")
                return None
            elif e.response.status_code == 429:
                logger.warning("ORS rate limit exceeded")
                # Continue retrying for rate limits
            elif 400 <= e.response.status_code < 500:
                logger.error(f"ORS client error {e.response.status_code}: {e.response.text}")
                return None
            
            # Retry for server errors (5xx) and rate limits
            if attempt == settings.ROUTING_MAX_RETRIES - 1:
                logger.error(f"ORS server error after {settings.ROUTING_MAX_RETRIES} attempts: {e}")
                return None
                
        except httpx.RequestError as e:
            logger.warning(f"ORS request error on attempt {attempt + 1}/{settings.ROUTING_MAX_RETRIES}: {e}")
            if attempt == settings.ROUTING_MAX_RETRIES - 1:
                logger.error(f"ORS request failed after {settings.ROUTING_MAX_RETRIES} attempts: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Unexpected ORS error on attempt {attempt + 1}/{settings.ROUTING_MAX_RETRIES}: {e}")
            if attempt == settings.ROUTING_MAX_RETRIES - 1:
                return None
        
        # Exponential backoff delay
        if attempt < settings.ROUTING_MAX_RETRIES - 1:
            delay = settings.ROUTING_RETRY_DELAY * (settings.ROUTING_RETRY_BACKOFF ** attempt)
            logger.debug(f"ORS retry delay: {delay:.1f}s")
            await asyncio.sleep(delay)
    
    logger.error(f"ORS failed after {settings.ROUTING_MAX_RETRIES} attempts")
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


async def test_ors_connectivity() -> Dict[str, Any]:
    """
    Test ORS connectivity with a known route.
    
    Returns:
        Dict with test results
    """
    if not settings.ORS_API_KEY:
        return {
            "status": "error",
            "error": "ORS_API_KEY not configured",
            "response_time_ms": 0
        }
    
    # Test route: Mumbai to Delhi
    mumbai = (19.0760, 72.8777)
    delhi = (28.7041, 77.1025)
    
    try:
        start_time = datetime.now()
        result = await get_route_ors(mumbai, delhi)
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
