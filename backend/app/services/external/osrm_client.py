import httpx
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.utils.exceptions import ExternalAPIError

settings = get_settings()


async def get_route_osrm(origin: str, destination: str) -> Optional[Dict[str, Any]]:
    """
    Query OSRM for route distance and duration.
    origin/destination: "lon,lat" strings.
    Returns dict with distance (meters) and duration (seconds).
    """
    url = f"{settings.OSRM_BASE_URL}/route/v1/driving/{origin};{destination}"
    params = {"overview": "false"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=settings.ROUTING_TIMEOUT_SECONDS)
            resp.raise_for_status()
            data = resp.json()
            if data.get("routes"):
                route = data["routes"][0]
                return {
                    "distance_m": route["distance"],
                    "duration_s": route["duration"],
                    "provider": "osrm",
                }
            else:
                return None
    except httpx.HTTPError as e:
        raise ExternalAPIError(f"OSRM request failed: {e}")
