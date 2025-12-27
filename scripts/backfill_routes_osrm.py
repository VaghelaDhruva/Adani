#!/usr/bin/env python3
"""
Backfill transport route distances using OSRM.
Iterates over transport_routes_modes and fills missing distance_km.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.services.external.osrm_client import get_route_osrm
from app.services.external.cache_service import cache_route
from app.db.base import SessionLocal
from app.db.models import TransportRoutesModes, PlantMaster


async def backfill():
    db = SessionLocal()
    try:
        # Fetch all routes with missing distance_km
        routes = db.query(TransportRoutesModes).filter(TransportRoutesModes.distance_km.is_(None)).all()
        plants = {p.plant_id: (p.longitude, p.latitude) for p in db.query(PlantMaster).all()}
        for r in routes:
            origin_coords = plants.get(r.origin_plant_id)
            if not origin_coords:
                print(f"Skipping route {r.id}: missing coordinates for origin {r.origin_plant_id}")
                continue
            # For now, assume destination is also a plant (extend later)
            dest_coords = plants.get(r.destination_node_id)
            if not dest_coords:
                print(f"Skipping route {r.id}: missing coordinates for destination {r.destination_node_id}")
                continue
            origin_str = f"{origin_coords[0]},{origin_coords[1]}"
            dest_str = f"{dest_coords[0]},{dest_coords[1]}"
            result = await get_route_osrm(origin_str, dest_str)
            if result:
                distance_km = result["distance_m"] / 1000.0
                duration_s = result["duration_s"]
                r.distance_km = distance_km
                # Cache result
                cache_route(origin_str, dest_str, distance_km, duration_s, "osrm", db)
                print(f"Filled distance for route {r.id}: {distance_km:.2f} km")
            else:
                print(f"No OSRM result for route {r.id}")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(backfill())
