"""
Background Job Queue Service

Implements async background job execution without Celery.
Uses SQLite for job persistence and FastAPI BackgroundTasks for execution.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks

from app.db.models.job_status import JobStatusTable, JobStatus
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class JobQueueService:
    """Service for managing background jobs with SQLite persistence."""
    
    def __init__(self):
        self.active_jobs: Dict[str, asyncio.Task] = {}
        self.max_concurrent_jobs = 3  # Limit concurrent optimization runs
        
    def submit_job(
        self,
        db: Session,
        job_type: str,
        job_function: Callable,
        scenario_name: Optional[str] = None,
        user_id: Optional[str] = None,
        **job_kwargs
    ) -> str:
        """
        Submit a job to the queue.
        
        Args:
            db: Database session
            job_type: Type of job (e.g., "optimization", "validation")
            job_function: Function to execute in background
            scenario_name: Optional scenario name
            user_id: Optional user ID
            **job_kwargs: Additional arguments to pass to job_function
            
        Returns:
            job_id: Unique job identifier
        """
        # Generate unique job ID
        job_id = f"{job_type.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Create job status record
        job_status = JobStatusTable(
            job_id=job_id,
            status=JobStatus.PENDING,
            submitted_time=datetime.now(),
            job_type=job_type,
            scenario_name=scenario_name,
            user_id=user_id,
            progress_percent=0,
            progress_message="Job queued"
        )
        
        db.add(job_status)
        db.commit()
        db.refresh(job_status)
        
        logger.info(f"Job {job_id} submitted and queued")
        
        return job_id
    
    def execute_job_async(
        self,
        db: Session,
        job_id: str,
        job_function: Callable,
        **job_kwargs
    ) -> None:
        """
        Execute job asynchronously with proper status tracking.
        
        This method should be called via FastAPI BackgroundTasks.
        """
        try:
            # Update status to RUNNING
            job_status = db.query(JobStatusTable).filter(JobStatusTable.job_id == job_id).first()
            if not job_status:
                logger.error(f"Job {job_id} not found in database")
                return
            
            job_status.status = JobStatus.RUNNING
            job_status.start_time = datetime.now()
            job_status.progress_percent = 10
            job_status.progress_message = "Job started"
            db.commit()
            
            logger.info(f"Job {job_id} started execution")
            
            # Execute the job function
            # Pass db session and job_id for status updates
            result = job_function(db=db, job_id=job_id, **job_kwargs)
            
            # Update status to SUCCESS
            job_status.status = JobStatus.SUCCESS
            job_status.end_time = datetime.now()
            job_status.progress_percent = 100
            job_status.progress_message = "Job completed successfully"
            
            if job_status.start_time:
                execution_time = (job_status.end_time - job_status.start_time).total_seconds()
                job_status.execution_time_seconds = execution_time
            
            # Store result reference if provided
            if isinstance(result, dict) and "result_ref" in result:
                job_status.result_ref = result["result_ref"]
            if isinstance(result, dict) and "result_data" in result:
                job_status.result_data = result.get("result_data")
            
            db.commit()
            
            logger.info(f"Job {job_id} completed successfully in {job_status.execution_time_seconds:.2f}s")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
            
            # Update status to FAILED
            job_status = db.query(JobStatusTable).filter(JobStatusTable.job_id == job_id).first()
            if job_status:
                job_status.status = JobStatus.FAILED
                job_status.end_time = datetime.now()
                job_status.error = str(e)
                job_status.error_details = {
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
                job_status.progress_message = f"Job failed: {str(e)}"
                
                if job_status.start_time:
                    execution_time = (job_status.end_time - job_status.start_time).total_seconds()
                    job_status.execution_time_seconds = execution_time
                
                db.commit()
    
    def update_job_progress(
        self,
        db: Session,
        job_id: str,
        progress_percent: int,
        progress_message: Optional[str] = None
    ) -> None:
        """Update job progress."""
        try:
            job_status = db.query(JobStatusTable).filter(JobStatusTable.job_id == job_id).first()
            if job_status:
                job_status.progress_percent = progress_percent
                if progress_message:
                    job_status.progress_message = progress_message
                job_status.updated_at = datetime.now()
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update job progress for {job_id}: {e}")
    
    def get_job_status(self, db: Session, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current job status."""
        job_status = db.query(JobStatusTable).filter(JobStatusTable.job_id == job_id).first()
        if not job_status:
            return None
        
        return {
            "job_id": job_status.job_id,
            "status": job_status.status.value,
            "submitted_time": job_status.submitted_time.isoformat() if job_status.submitted_time else None,
            "start_time": job_status.start_time.isoformat() if job_status.start_time else None,
            "end_time": job_status.end_time.isoformat() if job_status.end_time else None,
            "job_type": job_status.job_type,
            "scenario_name": job_status.scenario_name,
            "progress_percent": job_status.progress_percent,
            "progress_message": job_status.progress_message,
            "result_ref": job_status.result_ref,
            "error": job_status.error,
            "execution_time_seconds": job_status.execution_time_seconds
        }
    
    def cancel_job(self, db: Session, job_id: str) -> bool:
        """Cancel a pending or running job."""
        job_status = db.query(JobStatusTable).filter(JobStatusTable.job_id == job_id).first()
        if not job_status:
            return False
        
        if job_status.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            job_status.status = JobStatus.CANCELLED
            job_status.end_time = datetime.now()
            job_status.progress_message = "Job cancelled by user"
            db.commit()
            logger.info(f"Job {job_id} cancelled")
            return True
        
        return False


# Singleton instance
job_queue_service = JobQueueService()
