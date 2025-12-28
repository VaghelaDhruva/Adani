import logging

import pandas as pd
import pytest

from app.services.validation.rules import (
    reject_negative_demand,
    reject_illegal_routes,
    enforce_unit_consistency,
)
from app.services.validation.validators import validate_referential_integrity
from app.utils.exceptions import DataValidationError


def test_reject_negative_demand_raises_with_context():
    """Negative demand values should be rejected with contextual error message."""

    df = pd.DataFrame(
        [
            {"customer_node_id": "Mumbai", "period": "2025-03", "demand_tonnes": -12.0},
        ]
    )

    with pytest.raises(DataValidationError) as exc:
        reject_negative_demand(df)

    msg = str(exc.value)
    # Backward-compatible substring plus context
    assert "Negative demand values detected" in msg
    assert "Mumbai" in msg
    assert "2025-03" in msg
    assert "-12.0" in msg


def test_reject_illegal_routes_origin_equals_destination():
    """Routes where origin == destination must be rejected as illegal."""

    df = pd.DataFrame(
        [
            {
                "origin_plant_id": "P1",
                "destination_node_id": "P1",
                "transport_mode": "road",
                "vehicle_capacity_tonnes": 20.0,
            }
        ]
    )

    with pytest.raises(DataValidationError) as exc:
        reject_illegal_routes(df, origin_col="origin_plant_id", dest_col="destination_node_id")

    msg = str(exc.value)
    assert "Illegal routes detected" in msg
    assert "origin=P1" in msg
    assert "destination=P1" in msg


def test_missing_reference_rejected_via_referential_integrity(db_session):
    """Unknown node_id should be reported by referential-integrity checks when reference data exists."""

    # Arrange: create a known plant and a known demand customer to activate RI checks
    from app.db.models.plant_master import PlantMaster
    from app.db.models.demand_forecast import DemandForecast as DemandForecastModel

    db_session.add(PlantMaster(plant_id="P1", plant_name="Plant 1", plant_type="clinker"))
    db_session.add(
        DemandForecastModel(
            customer_node_id="C1",
            period="2025-01",
            demand_tonnes=100.0,
        )
    )
    db_session.commit()

    # Record references an unknown node_id (this should trigger RI validation)
    records = [
        {"node_id": "UNKNOWN_NODE", "policy_type": "min", "policy_value": 1.0},
    ]

    errors = validate_referential_integrity(db_session, records)
    assert errors, f"Expected validation errors, but got: {errors}"
    joined = " ; ".join(errors)
    assert "node_id not found" in joined
    assert "UNKNOWN_NODE" in joined


def test_referential_integrity_skipped_when_no_known_nodes(db_session):
    """When no plants or markets exist, RI checks should be skipped to preserve backward compatibility."""

    # No reference data created - this should skip RI validation
    records = [
        {"node_id": "UNKNOWN_NODE", "policy_type": "min", "policy_value": 1.0},
    ]

    errors = validate_referential_integrity(db_session, records)
    assert errors == [], f"Expected no errors when no reference data exists, but got: {errors}"


def test_logging_occurs_on_validation_failure():
    """Validation failures should raise appropriate errors with context."""

    df = pd.DataFrame(
        [
            {"customer_node_id": "C1", "period": "2025-01", "demand_tonnes": -5.0},
        ]
    )

    with pytest.raises(DataValidationError) as exc:
        reject_negative_demand(df)

    # Verify the error message contains expected context
    error_msg = str(exc.value)
    assert "Negative demand values detected" in error_msg
    assert "C1" in error_msg
    assert "2025-01" in error_msg
    assert "-5.0" in error_msg


def test_valid_dataset_passes_unit_consistency():
    """Valid, consistent units should not raise any errors."""

    df = pd.DataFrame(
        [
            {
                "customer_node_id": "C1",
                "period": "2025-01",
                "demand_tonnes": 10.0,
                "demand_unit": "tonne",
                "inventory_unit": "tonne",
                "cost_currency": "USD",
                "period_unit": "month",
            },
            {
                "customer_node_id": "C2",
                "period": "2025-02",
                "demand_tonnes": 15.0,
                "demand_unit": "tonne",
                "inventory_unit": "tonne",
                "cost_currency": "USD",
                "period_unit": "month",
            },
        ]
    )

    # Should not raise
    enforce_unit_consistency(df, mappings={})
