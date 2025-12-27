from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

# Placeholder audit log table; replace with real model later
class FakeAuditLog:
    def __init__(self, user: str, action: str, resource: str, details: Optional[Dict[str, Any]]):
        self.user = user
        self.action = action
        self.resource = resource
        self.details = details or {}
        self.timestamp = datetime.utcnow()


# In-memory stub for demo; replace with DB writes later
fake_audit_logs = []


def log_event(user: str, action: str, resource: str, details: Optional[Dict[str, Any]] = None):
    """Record an audit event."""
    entry = FakeAuditLog(user=user, action=action, resource=resource, details=details)
    fake_audit_logs.append(entry)


def get_audit_logs(db: Session, limit: int = 100) -> list:
    """Return recent audit logs (stub)."""
    return fake_audit_logs[-limit:]
