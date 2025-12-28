from typing import Dict, Any, Optional, List, Type

import pandas as pd
from sqlalchemy.orm import Session

from app.db.models.plant_master import PlantMaster
from app.db.models.production_capacity_cost import ProductionCapacityCost
from app.db.models.transport_routes_modes import TransportRoutesModes
from app.db.models.demand_forecast import DemandForecast as DemandForecastModel
from app.db.models.initial_inventory import InitialInventory as InitialInventoryModel
from app.db.models.safety_stock_policy import SafetyStockPolicy as SafetyStockPolicyModel
from app.schemas.plant import PlantMasterCreate
from app.schemas.demand import DemandForecastCreate
from app.schemas.transport import TransportRouteCreate
from app.schemas.inventory import SafetyStockPolicyCreate, InitialInventoryCreate
from app.services.validation.validators import (
    validate_schema,
    detect_missing_or_inconsistent,
    validate_referential_integrity,
    normalize_cost_units,
    normalize_demand_to_period,
)
from app.services.validation.rules import (
    reject_negative_demand,
    reject_illegal_routes,
    enforce_unit_consistency,
)
from app.services.audit_service import log_event
from app.utils.exceptions import DataValidationError


_TABLE_CONFIG = {
    "plant_master": {
        "required_columns": ["plant_id", "plant_name", "plant_type"],
        "schema": PlantMasterCreate,
        "model": PlantMaster,
    },
    "demand_forecast": {
        "required_columns": ["customer_node_id", "period", "demand_tonnes"],
        "schema": DemandForecastCreate,
        "model": DemandForecastModel,
    },
    "transport_routes_modes": {
        "required_columns": [
            "origin_plant_id",
            "destination_node_id",
            "transport_mode",
            "vehicle_capacity_tonnes",
        ],
        "schema": TransportRouteCreate,
        "model": TransportRoutesModes,
    },
    "safety_stock_policy": {
        "required_columns": ["node_id", "policy_type", "policy_value"],
        "schema": SafetyStockPolicyCreate,
        "model": SafetyStockPolicyModel,
    },
    "initial_inventory": {
        "required_columns": ["node_id", "period", "inventory_tonnes"],
        "schema": InitialInventoryCreate,
        "model": InitialInventoryModel,
    },
}


def _detect_table_name(df: pd.DataFrame, filename: str, explicit: Optional[str]) -> str:
    if explicit:
        if explicit not in _TABLE_CONFIG:
            raise DataValidationError(f"Unknown table_name '{explicit}'")
        return explicit

    # heuristic based on filename
    lowered = filename.lower()
    if lowered.startswith("plant"):
        candidate = "plant_master"
    elif lowered.startswith("demand"):
        candidate = "demand_forecast"
    elif lowered.startswith("route") or "transport" in lowered:
        candidate = "transport_routes_modes"
    elif "safety" in lowered:
        candidate = "safety_stock_policy"
    elif "inventory" in lowered:
        candidate = "initial_inventory"
    else:
        raise DataValidationError("Could not infer target table from filename; please specify table_name explicitly")

    cfg = _TABLE_CONFIG[candidate]
    errors = detect_missing_or_inconsistent(df, cfg["required_columns"])
    if errors:
        raise DataValidationError(
            f"File appears to target '{candidate}' but is missing required columns: {', '.join(errors)}"
        )
    return candidate


def _validate_and_normalize(
    df: pd.DataFrame,
    table_name: str,
    db: Session,
) -> List[Dict[str, Any]]:
    cfg = _TABLE_CONFIG[table_name]
    required_columns = cfg["required_columns"]

    # 1) basic column / missing checks
    errors = detect_missing_or_inconsistent(df, required_columns)
    if errors:
        raise DataValidationError("; ".join(errors))

    records = df.to_dict(orient="records")

    # 2) schema validation (Pydantic) before anything else
    schema_cls: Type = cfg["schema"]
    validated_records: List[Dict[str, Any]] = []
    for idx, row in enumerate(records):
        try:
            model = validate_schema(row, schema_cls)
            validated_records.append(model.dict())
        except DataValidationError as e:
            raise DataValidationError(f"Row {idx + 1}: {e}")

    # 3) referential integrity
    ref_errors = validate_referential_integrity(db, validated_records)
    if ref_errors:
        raise DataValidationError("; ".join(ref_errors))

    # 4) business rules (operate on validated records)
    # Convert back to DataFrame for rule functions that expect DataFrame
    validated_df = pd.DataFrame(validated_records)
    if table_name == "demand_forecast":
        validated_df = reject_negative_demand(validated_df)
        validated_df = normalize_demand_to_period(validated_df)
    if table_name == "transport_routes_modes":
        validated_df = reject_illegal_routes(validated_df, origin_col="origin_plant_id", dest_col="destination_node_id")
        validated_df = normalize_cost_units(validated_df)
    if table_name in {"safety_stock_policy", "initial_inventory"}:
        # no specific business rule yet, but keep hook for future
        pass

    # 5) unit consistency (no-op placeholder but keep call for future enforcement)
    validated_df = enforce_unit_consistency(validated_df, mappings={})

    return validated_df.to_dict(orient="records")


def ingest_dataframe(
    df: pd.DataFrame,
    db: Session,
    filename: str,
    explicit_table_name: Optional[str] = None,
    user: str = "ingestion-api",
) -> Dict[str, Any]:
    """Central orchestration for tabular ingestion.

    Handles table detection, validation, referential checks, DB writes, and audit logging.
    """

    if df is None or df.empty:
        raise DataValidationError("Input data is empty")

    table_name = _detect_table_name(df, filename, explicit_table_name)
    cfg = _TABLE_CONFIG[table_name]
    model_cls = cfg["model"]

    rows_attempted = len(df)
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
            raise
        raise
    finally:
        details: Dict[str, Any] = {
            "filename": filename,
            "table": table_name,
            "rows_attempted": rows_attempted,
            "rows_inserted": rows_inserted,
            "status": status,
        }
        if error_message:
            details["error"] = error_message
        log_event(user=user, action="csv_ingestion", resource=table_name, details=details)

    return {
        "filename": filename,
        "table": table_name,
        "rows_attempted": rows_attempted,
        "rows_inserted": rows_inserted,
        "status": status,
    }

