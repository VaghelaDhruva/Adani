from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.base import get_db
from app.schemas.scenario import ScenarioMetadata, ScenarioMetadataCreate, ScenarioMetadataUpdate

router = APIRouter()


@router.post("/", response_model=ScenarioMetadata)
def create_scenario(scenario: ScenarioMetadataCreate, db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/", response_model=List[ScenarioMetadata])
def list_scenarios(db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{scenario_name}", response_model=ScenarioMetadata)
def get_scenario(scenario_name: str, db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("/{scenario_name}", response_model=ScenarioMetadata)
def update_scenario(scenario_name: str, scenario: ScenarioMetadataUpdate, db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/{scenario_name}")
def delete_scenario(scenario_name: str, db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")
