import io
import pandas as pd

from app.db.models.demand_forecast import DemandForecast as DemandForecastModel


def _make_upload_file(tmp_path, filename: str, df: pd.DataFrame):
    from fastapi import UploadFile

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    file_obj = io.BytesIO(csv_bytes)
    return UploadFile(filename=filename, file=file_obj)


def test_upload_csv_rejects_negative_demand(client, db_session):
    df = pd.DataFrame(
        [
            {"customer_node_id": "C1", "period": "2025-01", "demand_tonnes": 100.0},
            {"customer_node_id": "C2", "period": "2025-01", "demand_tonnes": -5.0},
        ]
    )

    files = {"file": ("demand_bad.csv", df.to_csv(index=False), "text/csv")}
    response = client.post("/api/v1/data/upload_csv", files=files)

    assert response.status_code == 400
    assert "Negative demand values detected" in response.json()["detail"]


def test_upload_csv_rejects_missing_required_column(client, db_session):
    # Missing 'period' column
    df = pd.DataFrame(
        [
            {"customer_node_id": "C1", "demand_tonnes": 100.0},
        ]
    )

    files = {"file": ("demand_missing_col.csv", df.to_csv(index=False), "text/csv")}
    response = client.post("/api/v1/data/upload_csv", files=files)

    assert response.status_code == 400
    body = response.json()["detail"]
    assert "Missing required column" in body or "missing required columns" in body


def test_plant_master_schema_error(client, db_session):
    """Plant master with missing required column should be rejected."""
    df = pd.DataFrame(
        [
            {"plant_id": "P1"}  # missing plant_name, plant_type
        ]
    )
    files = {"file": ("plant_missing_cols.csv", df.to_csv(index=False), "text/csv")}
    response = client.post("/api/v1/data/upload_csv", files=files)

    assert response.status_code == 400
    body = response.json()
    assert "detail" in body
    assert any(err in body["detail"] for err in ["Missing required column", "missing required columns"])

    # Ensure no rows were inserted
    from app.db.models.plant_master import PlantMaster
    rows = db_session.query(PlantMaster).filter(PlantMaster.plant_id == "P1").all()
    assert len(rows) == 0


def test_transport_route_invalid_origin(client, db_session):
    """Transport route with unknown origin_plant_id should be rejected."""
    df = pd.DataFrame(
        [
            {
                "origin_plant_id": "UNKNOWN_PLANT",
                "destination_node_id": "C1",
                "transport_mode": "road",
                "vehicle_capacity_tonnes": 20.0,
            }
        ]
    )
    files = {"file": ("route_bad_origin.csv", df.to_csv(index=False), "text/csv")}
    response = client.post("/api/v1/data/upload_csv", files=files)

    assert response.status_code == 400
    body = response.json()
    assert "detail" in body
    assert "origin_plant_id not found in plant_master" in body["detail"]

    # Ensure no rows were inserted
    from app.db.models.transport_routes_modes import TransportRoutesModes
    rows = db_session.query(TransportRoutesModes).filter(TransportRoutesModes.origin_plant_id == "UNKNOWN_PLANT").all()
    assert len(rows) == 0


def test_safety_stock_policy_schema_error(client, db_session):
    """Safety stock policy with missing required column should be rejected."""
    df = pd.DataFrame(
        [
            {"node_id": "N1"}  # missing policy_type, policy_value
        ]
    )
    files = {"file": ("safety_missing_cols.csv", df.to_csv(index=False), "text/csv")}
    response = client.post("/api/v1/data/upload_csv", files=files)

    assert response.status_code == 400
    body = response.json()
    assert "detail" in body
    assert any(err in body["detail"] for err in ["Missing required column", "missing required columns"])

    # Ensure no rows were inserted
    from app.db.models.safety_stock_policy import SafetyStockPolicy
    rows = db_session.query(SafetyStockPolicy).filter(SafetyStockPolicy.node_id == "N1").all()
    assert len(rows) == 0


def test_initial_inventory_schema_error(client, db_session):
    """Initial inventory with missing required column should be rejected."""
    df = pd.DataFrame(
        [
            {"node_id": "N1"}  # missing period, inventory_tonnes
        ]
    )
    files = {"file": ("inventory_missing_cols.csv", df.to_csv(index=False), "text/csv")}
    response = client.post("/api/v1/data/upload_csv", files=files)

    assert response.status_code == 400
    body = response.json()
    assert "detail" in body
    assert any(err in body["detail"] for err in ["Missing required column", "missing required columns"])

    # Ensure no rows were inserted
    from app.db.models.initial_inventory import InitialInventory
    rows = db_session.query(InitialInventory).filter(InitialInventory.node_id == "N1").all()
    assert len(rows) == 0


def test_demand_forecast_happy_path(client, db_session):
    df = pd.DataFrame(
        [
            {"customer_node_id": "C1", "period": "2025-01", "demand_tonnes": 100.0},
            {"customer_node_id": "C1", "period": "2025-02", "demand_tonnes": 120.0},
        ]
    )

    files = {"file": ("demand_good.csv", df.to_csv(index=False), "text/csv")}
    response = client.post("/api/v1/data/upload_csv", files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["rows_attempted"] == 2
    assert body["rows_inserted"] == 2

    rows = (
        db_session.query(DemandForecastModel)
        .filter(DemandForecastModel.customer_node_id == "C1")
        .order_by(DemandForecastModel.period)
        .all()
    )
    assert len(rows) == 2
    assert rows[0].period == "2025-01"
    assert rows[0].demand_tonnes == 100.0
    assert rows[1].period == "2025-02"
    assert rows[1].demand_tonnes == 120.0
