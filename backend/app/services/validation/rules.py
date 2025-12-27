from typing import Any, List
from pandas import DataFrame

from app.utils.exceptions import DataValidationError


def reject_negative_demand(df: DataFrame, demand_col: str = "demand_tonnes") -> DataFrame:
    """Raise error if any demand values are negative."""
    if (df[demand_col] < 0).any():
        raise DataValidationError("Negative demand values detected")
    return df


def reject_illegal_routes(df: DataFrame, origin_col: str, dest_col: str) -> DataFrame:
    """
    Reject routes where origin == destination.
    Later: also reject disallowed mode-region combinations.
    """
    if (df[origin_col] == df[dest_col]).any():
        raise DataValidationError("Illegal routes detected (origin == destination)")
    return df


def enforce_unit_consistency(df: DataFrame, mappings: dict) -> DataFrame:
    """
    Ensure columns use expected units; raise if not.
    mappings: {col_name: expected_unit}
    """
    # Placeholder: implement unit checks or conversions
    return df


def log_validation_exceptions(errors: List[str]) -> None:
    """Log validation errors; can be extended to write to audit table."""
    for e in errors:
        print(f"Validation error: {e}")  # TODO: replace with logger
