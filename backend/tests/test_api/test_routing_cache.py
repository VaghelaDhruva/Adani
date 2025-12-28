import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.db.models.transport_lookup import TransportLookup
from app.db.base import get_db
from app.main import app


def _make_client_with_db(db_session):
    """Create a TestClient wired to use the provided db_session via get_db override."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_route_cache_miss_and_store(db_session, monkeypatch):
    """First request misses cache, calls external API, stores result."""
    # Ensure transport_lookup table exists in this test DB
    inspector = inspect(db_session.bind)
    print("Tables in test DB:", inspector.get_table_names())
    assert inspector.has_table("transport_lookup"), "transport_lookup table not found in test DB"

    client = _make_client_with_db(db_session)

    # Mock the external API to return a known result (async-compatible)
    async def fake_osrm(*args, **kwargs):
        return {"distance_m": 5000, "duration_s": 300, "provider": "osrm"}

    monkeypatch.setattr("app.services.routing_cache.get_route_osrm", fake_osrm)

    response = client.get(
        "/api/v1/data/route",
        params={"origin_plant_id": "P1", "destination_node_id": "C1"},
    )
    # Temporary debug output as requested
    print("response:", response.status_code, response.text)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["distance_km"] == 5.0
    assert data["duration_minutes"] == 5.0
    assert data["source"] == "OSRM"

    # Verify it was stored in the cache
    cached = (
        db_session.query(TransportLookup)
        .filter_by(
            origin_plant_id="P1",
            destination_node_id="C1",
            transport_mode="driving",
        )
        .one_or_none()
    )
    assert cached is not None, "Expected cache row not found"
    assert cached.distance_km == 5.0
    assert cached.duration_minutes == 5.0
    assert cached.source == "OSRM"

    app.dependency_overrides.clear()


def test_route_cache_hit(db_session, monkeypatch):
    """Second request hits cache without calling external API."""
    # Pre-populate cache
    cached = TransportLookup(
        origin_plant_id="P1",
        destination_node_id="C1",
        transport_mode="driving",
        distance_km=10.0,
        duration_minutes=12.0,
        source="OSRM",
    )
    db_session.add(cached)
    db_session.commit()

    client = _make_client_with_db(db_session)

    # Mock external API to ensure it's not called (async-compatible mocks)
    async def fake_osrm(*args, **kwargs):
        return {"distance_m": 9999, "duration_s": 999, "provider": "osrm"}

    async def fake_ors(*args, **kwargs):
        return {"distance_m": 9999, "duration_s": 999, "provider": "ors"}

    monkeypatch.setattr("app.services.routing_cache.get_route_osrm", fake_osrm)
    monkeypatch.setattr("app.services.routing_cache.get_route_ors", fake_ors)

    response = client.get(
        "/api/v1/data/route",
        params={"origin_plant_id": "P1", "destination_node_id": "C1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["distance_km"] == 10.0
    assert data["duration_minutes"] == 12.0
    assert data["source"] == "OSRM"

    # Ensure external APIs were not called: since we hit cache, fake_* should not be awaited.
    # We cannot easily assert call counts with monkeypatch, but behavior (no external effect) is enough here.

    app.dependency_overrides.clear()


def test_route_api_failure_returns_404(db_session, monkeypatch):
    """If external API fails and no cache, return 404."""
    client = _make_client_with_db(db_session)

    # Mock both APIs to raise exceptions from async functions
    async def failing_osrm(*args, **kwargs):
        raise Exception("OSRM down")

    async def failing_ors(*args, **kwargs):
        raise Exception("ORS down")

    monkeypatch.setattr("app.services.routing_cache.get_route_osrm", failing_osrm)
    monkeypatch.setattr("app.services.routing_cache.get_route_ors", failing_ors)

    response = client.get(
        "/api/v1/data/route",
        params={"origin_plant_id": "P1", "destination_node_id": "C1"},
    )
    assert response.status_code == 404
    assert "Route not found" in response.json()["detail"]

    app.dependency_overrides.clear()


def test_route_idempotent_insert(db_session, monkeypatch):
    """Duplicate requests do not create duplicate rows."""
    client = _make_client_with_db(db_session)

    # Mock external API to return a result (async-compatible)
    async def fake_osrm(*args, **kwargs):
        return {"distance_m": 8000, "duration_s": 480, "provider": "osrm"}

    monkeypatch.setattr("app.services.routing_cache.get_route_osrm", fake_osrm)

    # First request
    client.get(
        "/api/v1/data/route",
        params={"origin_plant_id": "P2", "destination_node_id": "C2"},
    )
    # Second request (should hit cache, but even if it calls API, insert should be ignored)
    client.get(
        "/api/v1/data/route",
        params={"origin_plant_id": "P2", "destination_node_id": "C2"},
    )

    rows = db_session.query(TransportLookup).filter(
        TransportLookup.origin_plant_id == "P2",
        TransportLookup.destination_node_id == "C2",
        TransportLookup.transport_mode == "driving",
    ).all()
    assert len(rows) == 1

    app.dependency_overrides.clear()
