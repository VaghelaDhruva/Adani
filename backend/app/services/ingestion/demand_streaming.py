import asyncio
import httpx
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.utils.exceptions import ExternalAPIError

settings = get_settings()


async def poll_demand_once(client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
    """
    Poll a single demand feed endpoint.
    Expected JSON format: { "node_id": "...", "period": "...", "demand_tonnes": ..., ... }
    """
    if not settings.DEMAND_POLL_URL:
        return None
    try:
        resp = await client.get(settings.DEMAND_POLL_URL, timeout=settings.ROUTING_TIMEOUT_SECONDS)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        raise ExternalAPIError(f"Demand poll failed: {e}")


async def demand_polling_loop(db: Session, interval_seconds: int = None):
    """
    Background task that polls demand endpoint at a regular interval.
    For now, logs fetched payload; later, validates and writes to DB.
    """
    interval = interval_seconds or settings.DEMAND_POLL_INTERVAL_SECONDS
    async with httpx.AsyncClient() as client:
        while True:
            try:
                payload = await poll_demand_once(client)
                if payload:
                    # TODO: validate schema, write to demand_forecast table
                    print(f"Polled demand payload: {payload}")
            except Exception as e:
                print(f"Error in demand polling: {e}")
            await asyncio.sleep(interval)
