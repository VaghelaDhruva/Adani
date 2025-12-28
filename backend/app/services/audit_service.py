import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog


logger = logging.getLogger(__name__)


@contextmanager
def audit_timer(user: str, action: str, db: Session, metadata: Optional[Dict[str, Any]] = None):
    """Context manager that times an operation and logs/audits it.

    Usage:
        with audit_timer("user1", "run_scenario", db, {"scenario_count": 3}) as timer:
            # ... do work ...
            timer.set_success()  # or timer.set_failure("error msg")
    """
    start = time.monotonic()
    status = "failure"
    details: Optional[str] = None

    class Timer:
        def set_success(self, extra_meta: Optional[Dict[str, Any]] = None):
            nonlocal status, details
            status = "success"
            if extra_meta:
                metadata.update(extra_meta)

        def set_failure(self, error_msg: str):
            nonlocal status, details
            status = "failure"
            details = error_msg

    timer = Timer()
    try:
        yield timer
    finally:
        duration_ms = int((time.monotonic() - start) * 1000)

        # Write structured log
        log_entry = {
            "user": user,
            "action": action,
            "status": status,
            "duration_ms": duration_ms,
            "metadata": metadata or {},
        }
        if details:
            log_entry["details"] = details

        if status == "success":
            logger.info("Action completed", extra=log_entry)
        else:
            logger.error("Action failed", extra=log_entry)

        # Write audit record (never allow audit failures to crash the operation)
        try:
            audit = AuditLog(
                user=user,
                action=action,
                status=status,
                duration_ms=duration_ms,
                context=metadata,  # Use context instead of metadata
                details=details,
            )
            db.add(audit)
            db.commit()
        except Exception as e:
            logger.warning("Failed to write audit record", extra={"error": str(e)})


def log_event(user: str, action: str, resource: str, details: Optional[Dict[str, Any]] = None):
    """Legacy compatibility shim for existing code."""
    logger.info(
        "Legacy audit event",
        extra={
            "user": user,
            "action": action,
            "resource": resource,
            "details": details or {},
        },
    )


def get_audit_logs(db: Session, limit: int = 100) -> list:
    """Return recent audit logs from the database."""
    return (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )
