from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db.base import get_db
from app.schemas.kpi import OptimizationResult

router = APIRouter()


@router.post("/run", response_model=OptimizationResult)
def run_optimization(
    scenario_name: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Trigger an optimization run for a given scenario.
    For now, returns a stub; later will enqueue a Celery job.
    """
    # TODO: enqueue Celery task with scenario_name
    # TODO: return job_id and status
    return OptimizationResult(
        scenario_name=scenario_name,
        status="queued",
        solver="cbc",
        details={"job_id": "placeholder"}
    )


@router.get("/status/{job_id}")
def get_optimization_status(job_id: str, db: Session = Depends(get_db)):
    """Check status of an async optimization job."""
    # TODO: query job status from Celery result backend
    return {"job_id": job_id, "status": "pending", "progress": 0}


@router.get("/result/{scenario_name}")
def get_optimization_result(scenario_name: str, db: Session = Depends(get_db)):
    """Fetch the latest result for a scenario."""
    # TODO: fetch from results table/files
    return {"scenario_name": scenario_name, "status": "not_found"}
