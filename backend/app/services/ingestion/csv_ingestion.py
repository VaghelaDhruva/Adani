import pandas as pd
from typing import Dict, Any, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.utils.exceptions import DataValidationError
from app.services.ingestion.tabular_ingestion import ingest_dataframe


async def ingest_csv(file: UploadFile, db: Session, table_name: Optional[str] = None) -> Dict[str, Any]:
    """Ingest a CSV file into the appropriate logical table.

    This is a thin adapter around the generic tabular ingestion pipeline:
    - reads the uploaded file into a pandas DataFrame
    - forwards to ingest_dataframe for table detection, validation, and DB insert
    """
    if not file.filename.lower().endswith(".csv"):
        raise DataValidationError("Only CSV files are supported")

    try:
        contents = await file.read()
        df = pd.read_csv(pd.io.common.StringIO(contents.decode("utf-8")))
    except Exception as e:
        raise DataValidationError(f"Failed to read CSV: {e}")

    if df.empty:
        raise DataValidationError("CSV is empty")

    return ingest_dataframe(df=df, db=db, filename=file.filename, explicit_table_name=table_name)
