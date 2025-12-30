from typing import Any, Dict, List

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import logging

from app.core.deps import get_db
from app.services.audit_service import audit_timer
from app.services.job_queue import celery_app, run_scenarios_task
from app.services.scenarios.scenario_generator import ScenarioConfig


logger = logging.getLogger(__name__)


router = APIRouter()


@router.post("/submit")
def submit_job(scenarios: List[ScenarioConfig], db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    PHASE 6: Execute optimization scenarios with proper user context.
    
    Runs multiple optimization scenarios and tracks execution with audit logging.
    User context will be integrated when authentication system is implemented.
    
    Accepts the same payload as the synchronous /scenarios/run endpoint and
    enqueues a Celery task that executes the batch scenario runner.
    """

    user = "system"  # PHASE 6: Will be replaced with real user from auth context
    metadata = {"scenario_count": len(scenarios), "scenario_names": [s.name for s in scenarios]}

    with audit_timer(user, "submit_job", db, metadata) as timer:
        try:
            # Convert validated Pydantic models to plain dicts for Celery serialization
            payload: List[Dict[str, Any]] = [cfg.model_dump() for cfg in scenarios]
            async_result = run_scenarios_task.apply_async(args=[payload])

            timer.set_success(extra_meta={"job_id": async_result.id})
            return {"job_id": async_result.id, "status": "submitted"}
        except Exception as e:
            logger.error("Failed to submit job", extra={"error": str(e)})
            timer.set_failure("Failed to submit job")
            raise HTTPException(status_code=500, detail="Failed to submit job") from None


@router.get("/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    PHASE 6: Get job status with proper user context.
    
    Retrieves job execution status with audit logging.
    User context will be integrated when authentication system is implemented.
    
    Poll the status of an asynchronous optimization job.

    Returns one of the standard Celery states (PENDING, STARTED, SUCCESS,
    FAILURE, RETRY, REVOKED). When SUCCESS, includes the task result, which
    mirrors the synchronous scenario engine response. When FAILURE, returns a
    sanitized error message without exposing internal stack traces.
    """

    user = "system"  # PHASE 6: Will be replaced with real user from auth context
    metadata = {"job_id": job_id}

    try:
        with audit_timer(user, "poll_job", db, metadata) as timer:
            try:
                result = AsyncResult(job_id, app=celery_app)

                # If the job is not found, treat as 404
                if result.id is None:
                    timer.set_failure("Job not found")
                    raise HTTPException(status_code=404, detail="Job not found")

                response: Dict[str, Any] = {"job_id": job_id, "status": result.state}

                if result.state == "SUCCESS":
                    response["result"] = result.result
                    timer.set_success()
                elif result.state == "FAILURE":
                    # Sanitize the exception message to avoid leaking stack traces
                    error_msg = getattr(result.result, "message", str(result.result))
                    response["error"] = error_msg
                    timer.set_failure(error_msg)
                else:
                    timer.set_success()  # PENDING/STARTED/RETRY are normal states

                return response
            except HTTPException:
                raise
            except Exception as e:
                logger.error("Failed to poll job status", extra={"job_id": job_id, "error": str(e)})
                timer.set_failure("Failed to poll job status")
                raise HTTPException(status_code=500, detail="Failed to poll job status") from None
    except Exception:
        # If audit logging fails, still try to return the job status
        logger.warning("Audit logging failed for job poll", extra={"job_id": job_id})
        result = AsyncResult(job_id, app=celery_app)
        
        if result.id is None:
            raise HTTPException(status_code=404, detail="Job not found")

        response: Dict[str, Any] = {"job_id": job_id, "status": result.state}
        if result.state == "SUCCESS":
            response["result"] = result.result
        elif result.state == "FAILURE":
            error_msg = getattr(result.result, "message", str(result.result))
            response["error"] = error_msg
        
        return response
