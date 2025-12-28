from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.base import get_db
from app.services.ingestion.csv_ingestion import ingest_csv
from app.services.ingestion.excel_ingestion import ingest_excel
from app.utils.exceptions import DataValidationError
from app.schemas.plant import PlantMaster, PlantMasterCreate, PlantMasterUpdate
from app.schemas.demand import DemandForecast, DemandForecastCreate, DemandForecastUpdate
from app.schemas.transport import TransportRoute, TransportRouteCreate, TransportRouteUpdate
from app.schemas.inventory import SafetyStockPolicy, SafetyStockPolicyCreate, SafetyStockPolicyUpdate, InitialInventory, InitialInventoryCreate, InitialInventoryUpdate

router = APIRouter()


# Placeholder CRUD stubs; actual service layer will be added later
@router.post("/plants/", response_model=PlantMaster)
def create_plant(plant: PlantMasterCreate, db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/plants/", response_model=List[PlantMaster])
def list_plants(db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/demand/", response_model=DemandForecast)
def create_demand(demand: DemandForecastCreate, db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/demand/", response_model=List[DemandForecast])
def list_demand(db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/transport_routes/", response_model=TransportRoute)
def create_transport_route(route: TransportRouteCreate, db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/transport_routes/", response_model=List[TransportRoute])
def list_transport_routes(db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/safety_stock/", response_model=SafetyStockPolicy)
def create_safety_stock(policy: SafetyStockPolicyCreate, db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/safety_stock/", response_model=List[SafetyStockPolicy])
def list_safety_stock(db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/initial_inventory/", response_model=InitialInventory)
def create_initial_inventory(inv: InitialInventoryCreate, db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/initial_inventory/", response_model=List[InitialInventory])
def list_initial_inventory(db: Session = Depends(get_db)):
    # TODO: implement service layer
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/upload_csv")
async def upload_csv(
    file: UploadFile = File(...),
    table_name: Optional[str] = Query(default=None, description="Optional logical table name override"),
    db: Session = Depends(get_db),
):
    """Ingest a CSV or Excel file into the appropriate logical table.

    The ingestion pipeline performs table detection, validation, referential
    checks, unit consistency enforcement, DB insert, and audit logging.
    """
    try:
        fname = file.filename.lower()
        if fname.endswith(".csv"):
            result = await ingest_csv(file=file, db=db, table_name=table_name)
        elif fname.endswith(".xlsx") or fname.endswith(".xls"):
            result = await ingest_excel(file=file, db=db, table_name=table_name)
        else:
            raise DataValidationError("Unsupported file type; only CSV and Excel are supported")
        return result
    except DataValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to ingest file")


@router.get("/route")
async def get_route(
    origin_plant_id: str,
    destination_node_id: str,
    transport_mode: str = "driving",
    db: Session = Depends(get_db),
):
    """Get route distance and duration with caching."""
    from app.services.routing_cache import get_route_with_cache
    result = await get_route_with_cache(db, origin_plant_id, destination_node_id, transport_mode)
    if result is None:
        raise HTTPException(status_code=404, detail="Route not found and external API unavailable")
    return result
