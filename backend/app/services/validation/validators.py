from typing import Any, Dict, List
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from app.utils.exceptions import DataValidationError


def validate_schema(data: Dict[str, Any], schema_class) -> Any:
    """
    Validate a dict against a Pydantic schema.
    Returns the validated model instance.
    """
    try:
        return schema_class(**data)
    except PydanticValidationError as e:
        raise DataValidationError(f"Schema validation failed: {e}")


def validate_referential_integrity(db: Session, records: List[Dict[str, Any]]) -> List[str]:
    """Ensure foreign keys and identifiers refer to known entities.

    The checks are intentionally conservative to avoid breaking existing
    workflows: a rule is only enforced when reference data exists in the
    database, so empty dimension tables do not cause false positives.
    """
    errors: List[str] = []
    if not records:
        return errors

    first = records[0]

    # 1) Transport routes: origin_plant_id must exist in plant_master
    if "origin_plant_id" in first:
        from app.db.models.plant_master import PlantMaster

        origin_ids = {r["origin_plant_id"] for r in records if r.get("origin_plant_id")}
        if origin_ids:
            existing = {
                row.plant_id
                for row in db.query(PlantMaster.plant_id).filter(PlantMaster.plant_id.in_(origin_ids)).all()
            }
            missing = sorted(origin_ids - existing)
            if missing:
                errors.append(
                    f"origin_plant_id not found in plant_master: {', '.join(missing)}"
                )

    # 2) Transport routes: destination_node_id should refer to a known plant or market.
    # "Markets" are approximated here as demand/customer nodes.
    if "destination_node_id" in first:
        from app.db.models.plant_master import PlantMaster
        from app.db.models.demand_forecast import DemandForecast

        dest_ids = {r["destination_node_id"] for r in records if r.get("destination_node_id")}
        if dest_ids:
            plant_nodes = {
                row.plant_id
                for row in db.query(PlantMaster.plant_id)
                .filter(PlantMaster.plant_id.in_(dest_ids))
                .all()
            }
            market_nodes = {
                row.customer_node_id
                for row in db.query(DemandForecast.customer_node_id)
                .filter(DemandForecast.customer_node_id.in_(dest_ids))
                .all()
            }
            known_nodes = plant_nodes | market_nodes
            # Only enforce if we have any known nodes configured; otherwise assume
            # metadata is incomplete and skip to preserve backward compatibility.
            if known_nodes:
                missing_dest = sorted(dest_ids - known_nodes)
                if missing_dest:
                    errors.append(
                        "destination_node_id not found in known plants/markets: "
                        + ", ".join(missing_dest)
                    )

    # 3) Generic node_id checks for inventory / safety stock against known nodes
    if "node_id" in first:
        from app.db.models.plant_master import PlantMaster
        from app.db.models.demand_forecast import DemandForecast

        node_ids = {r["node_id"] for r in records if r.get("node_id")}
        if node_ids:
            # Check if we have any reference data at all (to activate RI)
            any_plants = db.query(PlantMaster).first() is not None
            any_markets = db.query(DemandForecast).first() is not None
            
            if any_plants or any_markets:
                plant_nodes = {
                    row.plant_id
                    for row in db.query(PlantMaster.plant_id)
                    .filter(PlantMaster.plant_id.in_(node_ids))
                    .all()
                }
                market_nodes = {
                    row.customer_node_id
                    for row in db.query(DemandForecast.customer_node_id)
                    .filter(DemandForecast.customer_node_id.in_(node_ids))
                    .all()
                }
                known_nodes = plant_nodes | market_nodes
                missing_nodes = sorted(node_ids - known_nodes)
                if missing_nodes:
                    errors.append(
                        "node_id not found in known plants/markets: "
                        + ", ".join(missing_nodes)
                    )

    return errors


def detect_missing_or_inconsistent(df, required_columns: List[str]) -> List[str]:
    """
    Detect missing values or obvious inconsistencies in a DataFrame.
    Return list of error messages.
    """
    errors = []
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
        else:
            missing = df[col].isna().sum()
            if missing:
                errors.append(f"Column {col} has {missing} missing values")
    return errors


def normalize_cost_units(df: Any) -> Any:
    """
    Normalize cost columns to a common unit (e.g., USD/tonne).
    Placeholder for real conversion logic.
    """
    # TODO: detect currency/unit columns and normalize
    return df


def normalize_demand_to_period(df: Any, period_freq: str = "W") -> Any:
    """
    Ensure demand is expressed per target period (daily/weekly/monthly).
    Placeholder for real aggregation logic.
    """
    # TODO: resample/aggregate if needed
    return df
