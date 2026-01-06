from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=True, index=True)
    user = Column(String(255), nullable=False, index=True)  # Username for backward compatibility
    action = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)  # success, failure
    duration_ms = Column(Integer, nullable=True)  # elapsed time in milliseconds
    context = Column(JSON, nullable=True)  # structured context, non-sensitive only (renamed from metadata)
    details = Column(Text, nullable=True)  # optional human-readable details
    
    # Node-level filtering info
    accessed_ius = Column(JSON, nullable=True)  # IUs accessed in this action
    accessed_gus = Column(JSON, nullable=True)  # GUs accessed in this action
    
    # Relationships
    user_obj = relationship("User", back_populates="audit_logs")
