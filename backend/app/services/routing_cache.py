from typing import Dict, Any, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.transport_lookup import TransportLookup
from app.services.external.osrm_client import get_route_osrm
from app.services.external.ors_client import get_route_ors
from app.core.config import get_settings

settings = get_settings()


async def get_route_with_cache(
    db: Session,
    origin_plant_id: str,
    destination_node_id: str,
    transport_mode: str = "driving",
) -> Optional[Dict[str, Any]]:
    """
    Get route distance and duration with caching.
    1) Check transport_lookup table first.
    2) If found, return cached distance_km and duration_minutes.
    3) If not found, call OSRM (or ORS if configured), store result, then return.
    Returns dict with distance_km, duration_minutes, source.
    """
    # 1) Check cache
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
        return {
            "distance_km": cached.distance_km,
            "duration_minutes": cached.duration_minutes,
            "source": cached.source,
        }

    # 2) Not cached: fetch from external API
    # For now, we assume origin/destination are lat,lon strings or lists
    # In future, resolve plant_id/customer_node_id to coordinates via geocode tables
    # Placeholder: use dummy coordinates to trigger API call for caching demo
    origin_coords = "0.0,0.0"  # TODO: resolve from plant_id
    dest_coords = "0.0,0.0"    # TODO: resolve from destination_node_id

    result = None
    provider = None
    if settings.ORS_API_KEY and settings.ORS_BASE_URL:
        # Prefer ORS if available
        try:
            result = await get_route_ors([0.0, 0.0], [0.0, 0.0])
            provider = "ORS"
        except Exception:
            # Fallback to OSRM
            try:
                result = await get_route_osrm(origin_coords, dest_coords)
                provider = "OSRM"
            except Exception:
                return None
    else:
        # Use OSRM
        try:
            result = await get_route_osrm(origin_coords, dest_coords)
            provider = "OSRM"
        except Exception:
            return None

    if not result:
        return None

    # 3) Store in cache (idempotent via unique constraint)
    distance_km = result.get("distance_m", 0) / 1000.0
    duration_minutes = result.get("duration_s", 0) / 60.0

    try:
        cache_entry = TransportLookup(
            origin_plant_id=origin_plant_id,
            destination_node_id=destination_node_id,
            transport_mode=transport_mode,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            source=provider,
        )
        db.add(cache_entry)
        db.commit()
    except IntegrityError:
        # Duplicate (origin, destination, mode) – safe to ignore for idempotency
        db.rollback()
    except Exception:
        # Any other failure should not break the caller; just rollback and return the live result
        db.rollback()

    return {
        "distance_km": distance_km,
        "duration_minutes": duration_minutes,
        "source": provider,
    }
