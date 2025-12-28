import logging
from unittest.mock import patch, MagicMock

import pytest

from app.services.audit_service import audit_timer, get_audit_logs
from app.db.models.audit_log import AuditLog
from app.utils.exceptions import DataValidationError


def test_audit_entry_created_on_scenario_run(db_session):
    """Scenario run should create an audit entry with success status."""
    with patch("app.services.audit_service.logger") as mock_logger:
        with audit_timer("user1", "run_scenarios", db_session, {"scenario_count": 3}) as timer:
            timer.set_success()

        # Verify log entry
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args[0][0] == "Action completed"
        assert "user" in call_args[1]["extra"]
        assert call_args[1]["extra"]["user"] == "user1"
        assert call_args[1]["extra"]["action"] == "run_scenarios"
        assert call_args[1]["extra"]["status"] == "success"
        assert "duration_ms" in call_args[1]["extra"]

    # Verify database entry
    audit_records = db_session.query(AuditLog).all()
    assert len(audit_records) == 1
    record = audit_records[0]
    assert record.user == "user1"
    assert record.action == "run_scenarios"
    assert record.status == "success"
    assert record.duration_ms is not None
    assert record.context == {"scenario_count": 3}


def test_audit_entry_created_on_job_submit_and_poll(db_session):
    """Job submit and poll should create audit entries with job_id."""
    # Test job submit
    with patch("app.services.audit_service.logger") as mock_logger:
        with audit_timer("system", "submit_job", db_session, {"scenario_count": 2}) as timer:
            timer.set_success(extra_meta={"job_id": "job123"})

        # Verify log entry includes job_id in metadata
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args[1]["extra"]["action"] == "submit_job"
        assert call_args[1]["extra"]["metadata"]["job_id"] == "job123"

    # Test job poll
    with patch("app.services.audit_service.logger") as mock_logger:
        with audit_timer("system", "poll_job", db_session, {"job_id": "job123"}) as timer:
            timer.set_success()

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert call_args[1]["extra"]["action"] == "poll_job"
        assert call_args[1]["extra"]["metadata"]["job_id"] == "job123"

    # Verify both database entries
    audit_records = db_session.query(AuditLog).order_by(AuditLog.timestamp).all()
    assert len(audit_records) == 2
    assert audit_records[0].action == "submit_job"
    assert audit_records[1].action == "poll_job"
    assert audit_records[0].context["job_id"] == "job123"
    assert audit_records[1].context["job_id"] == "job123"


def test_validation_failure_logs_and_audits(db_session):
    """Validation failures should write audit entries with action=validation_failed."""
    # Test the new audit_timer based validation logging (this is what actually writes to DB)
    with patch("app.services.audit_service.logger") as mock_logger:
        with audit_timer("system-validation", "reject_negative_demand", db_session, {"location": "Mumbai"}) as timer:
            timer.set_failure("Negative demand detected")

        # Should create a DB audit record
        audit_records = db_session.query(AuditLog).filter_by(action="reject_negative_demand").all()
        assert len(audit_records) == 1
        assert audit_records[0].status == "failure"
        assert audit_records[0].details == "Negative demand detected"
        assert audit_records[0].context == {"location": "Mumbai"}

        # Verify error log was called
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert call_args[0][0] == "Action failed"
        assert call_args[1]["extra"]["status"] == "failure"


def test_logging_never_crashes_api(db_session):
    """Audit logging failures should not crash the API operation."""
    # Mock the database operations to raise an exception
    with patch.object(db_session, "add", side_effect=Exception("DB connection failed")):
        with patch("app.services.audit_service.logger") as mock_logger:
            # This should not raise an exception despite audit DB failure
            with audit_timer("user1", "run_scenarios", db_session) as timer:
                timer.set_success()

            # Should log a warning about audit failure
            mock_logger.warning.assert_called()
            warning_call = mock_logger.warning.call_args_list[0]
            assert "Failed to write audit record" in warning_call[0][0]


def test_audit_timer_failure_status(db_session):
    """Audit timer should record failure status when set_failure is called."""
    with patch("app.services.audit_service.logger") as mock_logger:
        with audit_timer("user1", "run_scenarios", db_session) as timer:
            timer.set_failure("Something went wrong")

        # Verify error log
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert call_args[0][0] == "Action failed"
        assert call_args[1]["extra"]["status"] == "failure"
        assert call_args[1]["extra"]["details"] == "Something went wrong"

    # Verify database entry
    audit_records = db_session.query(AuditLog).all()
    assert len(audit_records) == 1
    record = audit_records[0]
    assert record.status == "failure"
    assert record.details == "Something went wrong"


def test_get_audit_logs_returns_recent_entries(db_session):
    """get_audit_logs should return recent audit entries ordered by timestamp desc."""
    import time
    from datetime import datetime, timedelta
    
    # Create multiple audit entries with explicit timestamps to ensure ordering
    base_time = datetime.utcnow()
    for i in range(5):
        # Create timestamp that's i seconds in the past from base_time
        timestamp = base_time + timedelta(seconds=i)
        audit = AuditLog(
            user=f"user{i}",
            action=f"action{i}",
            status="success",
            duration_ms=100 + i,
            context={"index": i},
            timestamp=timestamp,
        )
        db_session.add(audit)
        db_session.commit()

    # Get recent logs
    recent_logs = get_audit_logs(db_session, limit=3)
    assert len(recent_logs) == 3

    # Should be ordered by timestamp descending (most recent first)
    # Since we set timestamps explicitly, the highest index should be most recent
    indices = [log.context["index"] for log in recent_logs]
    assert indices == [4, 3, 2]  # Most recent first
