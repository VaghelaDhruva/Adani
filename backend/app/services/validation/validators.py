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
    """
    Ensure foreign keys exist (e.g., plant_id in plant_master).
    Return list of error messages.
    """
    errors = []
    # TODO: implement referential checks per entity type
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
