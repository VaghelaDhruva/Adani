from typing import Any, Dict, List, Optional
from pandas import DataFrame
import logging

from app.services.audit_service import log_event
from app.utils.exceptions import DataValidationError


def reject_negative_demand(df: DataFrame, demand_col: str = "demand_tonnes") -> DataFrame:
    """Raise error if any demand values are negative.

    Includes basic context (e.g. customer_node_id, period) in the error
    message when those columns are present, while preserving the original
    "Negative demand values detected" text for backward compatibility.
    """
    mask = df[demand_col] < 0
    if mask.any():
        first_idx = df.index[mask][0]
        row = df.loc[first_idx]
        location = row.get("customer_node_id") or row.get("node_id")
        period = row.get("period")
        value = row[demand_col]
        parts: List[str] = ["Negative demand values detected"]
        context_bits: List[str] = []
        if location is not None:
            context_bits.append(f"location={location}")
        if period is not None:
            context_bits.append(f"period={period}")
        context_bits.append(f"value={value}")
        parts.append(": ")
        parts.append(", ".join(context_bits))
        message = "".join(parts)
        _log_validation_failure(
            "reject_negative_demand",
            {"location": str(location), "period": str(period), "value": float(value)},
        )
        raise DataValidationError(message)
    return df


def reject_illegal_routes(df: DataFrame, origin_col: str, dest_col: str) -> DataFrame:
    """Reject obvious illegal routes at the row level.

    Currently checks for origin == destination. More complex checks that
    require database lookups (e.g. unknown plants or markets) are handled in
    the referential-integrity validator to keep concerns separated.
    """
    mask = df[origin_col] == df[dest_col]
    if mask.any():
        first_idx = df.index[mask][0]
        row = df.loc[first_idx]
        message = (
            "Illegal routes detected (origin == destination): "
            f"origin={row.get(origin_col)}, destination={row.get(dest_col)}"
        )
        _log_validation_failure(
            "reject_illegal_routes",
            {"origin": row.get(origin_col), "destination": row.get(dest_col)},
        )
        raise DataValidationError(message)
    return df


def enforce_unit_consistency(df: DataFrame, mappings: dict) -> DataFrame:
    """Ensure basic unit consistency when unit columns are present.

    This function is intentionally conservative to avoid breaking existing
    flows. It only raises when it can clearly detect mixed units within the
    same logical quantity (e.g., multiple currencies or quantity units).
    """
    unit_columns = [
        "demand_unit",
        "inventory_unit",
        "cost_currency",
        "period_unit",
    ]
    for col in unit_columns:
        if col in df.columns:
            unique_values = sorted({v for v in df[col].dropna().unique()})
            if len(unique_values) > 1:
                message = f"Mixed units detected in {col}: {unique_values}"
                _log_validation_failure(
                    "enforce_unit_consistency",
                    {"column": col, "values": [str(v) for v in unique_values]},
                )
                raise DataValidationError(message)
    return df


def log_validation_exceptions(errors: List[str]) -> None:
    """Log one or more validation error messages in a structured way."""
    for msg in errors:
        _log_validation_failure("validation_error", {"message": msg})


def _log_validation_failure(rule: str, details: Dict[str, Any]) -> None:
    logger = logging.getLogger(__name__)
    logger.warning("Validation failed for %s", rule, extra={"details": details})
    try:
        # Use legacy log_event for compatibility with existing validation code
        from app.services.audit_service import log_event
        log_event(
            user="system-validation",
            action="validation_failed",
            resource=rule,
            details=details,
        )
    except Exception:
        # Logging must never break validation; swallow any audit logging issues.
        pass
