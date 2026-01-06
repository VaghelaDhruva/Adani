"""
Job Status Model for Background Task Tracking

Tracks optimization jobs with proper lifecycle states:
PENDING → RUNNING → SUCCESS / FAILED
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

from app.db.base import Base


class JobStatus(str, enum.Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStatusTable(Base):
    """Job status tracking table for background optimization tasks."""
    
    __tablename__ = "job_status"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Status tracking
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING, index=True)
    
    # Timing
    submitted_time = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    
    # Job metadata
    job_type = Column(String(100), nullable=False)  # "optimization", "validation", etc.
    scenario_name = Column(String(255), nullable=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    
    # Results reference
    result_ref = Column(String(255), nullable=True)  # Reference to optimization_run.run_id or other result table
    result_data = Column(JSON, nullable=True)  # Store lightweight result summary
    
    # Error handling
    error = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)  # Structured error information
    
    # Progress tracking
    progress_percent = Column(Integer, default=0)
    progress_message = Column(String(500), nullable=True)
    
    # Performance metrics
    execution_time_seconds = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

