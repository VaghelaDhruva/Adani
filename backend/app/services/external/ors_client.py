import httpx
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.utils.exceptions import ExternalAPIError

settings = get_settings()


async def get_route_ors(origin: list, destination: list) -> Optional[Dict[str, Any]]:
    """
    Query OpenRouteService for route distance and duration.
    origin/destination: [lon, lat] lists.
    Returns dict with distance (meters) and duration (seconds).
    """
    if not settings.ORS_API_KEY:
        raise ExternalAPIError("ORS_API_KEY not configured")
    url = f"{settings.ORS_BASE_URL}/v2/directions/driving-car"
    headers = {"Authorization": f"Bearer {settings.ORS_API_KEY}"}
    params = {
        "start": f"{origin[0]},{origin[1]}",
        "end": f"{destination[0]},{destination[1]}",
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, params=params, timeout=settings.ROUTING_TIMEOUT_SECONDS)
            resp.raise_for_status()
            data = resp.json()
            if data.get("features"):
                props = data["features"][0]["properties"]
                summary = props.get("segments", [{}])[0].get("summary", {})
                return {
                    "distance_m": summary.get("distance"),
                    "duration_s": summary.get("duration"),
                    "provider": "ors",
                }
            else:
                return None
    except httpx.HTTPError as e:
        raise ExternalAPIError(f"ORS request failed: {e}")
