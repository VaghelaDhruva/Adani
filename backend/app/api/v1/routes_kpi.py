from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.base import get_db
from app.schemas.kpi import KPIDashboard, ScenarioComparison

router = APIRouter()


@router.get("/dashboard/{scenario_name}", response_model=KPIDashboard)
def get_kpi_dashboard(scenario_name: str, db: Session = Depends(get_db)):
    """Return KPIs for a given scenario."""
    # TODO: compute or fetch KPIs from results
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/compare", response_model=ScenarioComparison)
def compare_scenarios(scenario_names: List[str], db: Session = Depends(get_db)):
    """Compare KPIs across multiple scenarios."""
    # TODO: fetch and aggregate KPIs for each scenario
    raise HTTPException(status_code=501, detail="Not implemented")
