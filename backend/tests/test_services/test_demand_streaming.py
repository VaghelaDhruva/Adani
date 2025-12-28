import pytest
from sqlalchemy import select

from app.db.models.demand_forecast import DemandForecast
from app.services.ingestion.demand_streaming import ingest_streaming_demand_event
from app.utils.exceptions import DataValidationError


def test_valid_streaming_event(db_session):
    """Valid demand event should insert one row."""

    payload = {
        "customer_node_id": "C1",
        "period": "2025-01",
        "demand_tonnes": 100,
    }

    result = ingest_streaming_demand_event(payload, db=db_session)

    assert result["status"] == "success"
    assert result["rows_attempted"] == 1
    assert result["rows_inserted"] == 1

    rows = (
        db_session.execute(
            select(DemandForecast).where(
                DemandForecast.customer_node_id == "C1",
                DemandForecast.period == "2025-01",
            )
        )
        .scalars()
        .all()
    )

    assert len(rows) == 1
    assert rows[0].demand_tonnes == 100


def test_invalid_negative_demand_raises(db_session):
    """Negative demand should raise and not insert."""

    payload = {
        "customer_node_id": "C1",
        "period": "2025-01",
        "demand_tonnes": -1,
    }

    with pytest.raises(DataValidationError):
        ingest_streaming_demand_event(payload, db=db_session)

    rows = (
        db_session.execute(
            select(DemandForecast).where(
                DemandForecast.customer_node_id == "C1",
            )
        )
        .scalars()
        .all()
    )

    assert len(rows) == 0
