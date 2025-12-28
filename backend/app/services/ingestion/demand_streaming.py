import asyncio
import httpx
from typing import Dict, Any, Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.ingestion.tabular_ingestion import _TABLE_CONFIG, _validate_and_normalize
from app.services.audit_service import log_event
from app.utils.exceptions import ExternalAPIError, DataValidationError

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


def ingest_streaming_demand_event(payload: Dict[str, Any], db: Session, user: str = "demand-stream") -> Dict[str, Any]:
    """Validate and persist a single streaming demand event into demand_forecast.

    Reuses the same validation pipeline as CSV ingestion:
      1) schema validation (Pydantic)
      2) referential-integrity validation
      3) business-rule validation (negative demand, normalization)

    Raises DataValidationError on validation issues and guarantees 0 rows
    inserted in that case (transaction rollback).
    """
    table_name = "demand_forecast"
    cfg = _TABLE_CONFIG[table_name]
    model_cls = cfg["model"]

    # Map payload into the expected logical columns
    record = {
        "customer_node_id": payload.get("customer_node_id") or payload.get("node_id"),
        "period": payload.get("period"),
        "demand_tonnes": payload.get("demand_tonnes"),
    }

    df = pd.DataFrame([record])

    rows_attempted = 1
    rows_inserted = 0
    status = "failed"
    error_message: Optional[str] = None

    try:
        validated_records = _validate_and_normalize(df, table_name, db)
        instances = [model_cls(**rec) for rec in validated_records]
        db.add_all(instances)
        db.commit()
        rows_inserted = len(instances)
        status = "success"
    except Exception as e:
        db.rollback()
        error_message = str(e)
        if isinstance(e, DataValidationError):
            # Propagate structured validation error to caller
            raise
        # Re-raise unexpected errors so callers can handle/log as needed
        raise
    finally:
        details: Dict[str, Any] = {
            "source": "streaming",
            "table": table_name,
            "rows_attempted": rows_attempted,
            "rows_inserted": rows_inserted,
            "status": status,
        }
        if error_message:
            details["error"] = error_message
        log_event(user=user, action="demand_streaming", resource=table_name, details=details)

    return {
        "status": status,
        "rows_attempted": rows_attempted,
        "rows_inserted": rows_inserted,
    }


async def demand_polling_loop(db: Session, interval_seconds: int = None):
    """
    Background task that polls demand endpoint at a regular interval and
    validates + writes streaming demand events into demand_forecast.
    """
    interval = interval_seconds or settings.DEMAND_POLL_INTERVAL_SECONDS
    async with httpx.AsyncClient() as client:
        while True:
            try:
                payload = await poll_demand_once(client)
                if payload:
                    try:
                        result = ingest_streaming_demand_event(payload, db)
                        # Simple observability for now; could be structured logging later
                        print(f"Ingested streaming demand: {result}")
                    except DataValidationError as ve:
                        # Validation failure: 0 rows inserted by contract
                        print(f"Validation error in streaming demand: {ve}")
                    except Exception as e:
                        # Unexpected failure: nothing should have been committed
                        print(f"Error persisting streaming demand: {e}")
            except Exception as e:
                print(f"Error in demand polling: {e}")
            await asyncio.sleep(interval)
