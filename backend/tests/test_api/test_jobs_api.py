from typing import Any, Dict, List

from fastapi import status


class _FakeAsyncResult:
    def __init__(self, task_id: str, state: str, result: Any = None, info: Any = None) -> None:
        self.id = task_id
        self.status = state
        self.state = state  # Add state property to match Celery's AsyncResult
        self.result = result
        self.info = info


def test_submit_job_returns_job_id_and_status(client, monkeypatch):
    """POST /api/v1/jobs/submit returns a job_id and submitted status."""

    class _FakeTask:
        def __init__(self) -> None:
            self._id = "fake-task-id"

        def apply_async(self, args: List[Dict[str, Any]]):  # type: ignore[override]
            return _FakeAsyncResult(self._id, state="PENDING")

    # Patch the Celery task used by the jobs router
    monkeypatch.setattr(
        "app.api.v1.routes_jobs.run_scenarios_task",
        _FakeTask(),
    )

    payload = [{"name": "base", "type": "base"}]
    resp = client.post("/api/v1/jobs/submit", json=payload)

    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["status"] == "submitted"
    assert isinstance(body["job_id"], str)
    assert body["job_id"] == "fake-task-id"


def test_get_job_status_success(client, monkeypatch):
    """GET /api/v1/jobs/{job_id} returns SUCCESS with result when task completed."""

    fake_result_payload = {"scenarios": [{"name": "base", "status": "completed"}]}

    def _fake_async_result(job_id: str, app=None):  # type: ignore[override]
        return _FakeAsyncResult(job_id, state="SUCCESS", result=fake_result_payload)

    monkeypatch.setattr("app.api.v1.routes_jobs.AsyncResult", _fake_async_result)

    resp = client.get("/api/v1/jobs/some-id")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["status"] == "SUCCESS"
    assert body["job_id"] == "some-id"
    assert body["result"] == fake_result_payload


def test_get_job_status_failure(client, monkeypatch):
    """GET /api/v1/jobs/{job_id} exposes a safe FAILURE error message."""

    def _fake_async_result(job_id: str, app=None):  # type: ignore[override]
        return _FakeAsyncResult(job_id, state="FAILURE", result=Exception("solver failed"))

    monkeypatch.setattr("app.api.v1.routes_jobs.AsyncResult", _fake_async_result)

    resp = client.get("/api/v1/jobs/bad-id")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["status"] == "FAILURE"
    assert body["job_id"] == "bad-id"
    assert "solver failed" in body["error"]


def test_get_job_status_unknown_job_returns_404(client, monkeypatch):
    """Unknown job_id should return 404 Job not found."""

    def _fake_async_result(job_id: str, app=None):  # type: ignore[override]
        # Simulate Celery returning a completely empty meta for unknown IDs
        # Set id=None to indicate the job doesn't exist
        fake_result = _FakeAsyncResult(job_id, state="PENDING", result=None, info=None)
        fake_result.id = None  # Override to simulate unknown job
        return fake_result

    monkeypatch.setattr("app.api.v1.routes_jobs.AsyncResult", _fake_async_result)

    resp = client.get("/api/v1/jobs/does-not-exist")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    body = resp.json()
    assert body["detail"] == "Job not found"
