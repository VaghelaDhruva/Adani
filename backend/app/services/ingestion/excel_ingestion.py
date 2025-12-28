import pandas as pd
from typing import Dict, Any, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.utils.exceptions import DataValidationError
from app.services.ingestion.tabular_ingestion import ingest_dataframe


async def ingest_excel(file: UploadFile, db: Session, table_name: Optional[str] = None) -> Dict[str, Any]:
    """Ingest an Excel file into the appropriate logical table.

    Reads the uploaded Excel file into a pandas DataFrame and delegates to the
    generic tabular ingestion pipeline.
    """
    fname = file.filename.lower()
    if not (fname.endswith(".xlsx") or fname.endswith(".xls")):
        raise DataValidationError("Only Excel files (.xlsx/.xls) are supported")

    try:
        contents = await file.read()
        df = pd.read_excel(pd.io.common.BytesIO(contents))
    except Exception as e:
        raise DataValidationError(f"Failed to read Excel: {e}")

    if df.empty:
        raise DataValidationError("Excel file is empty or unreadable")

    return ingest_dataframe(df=df, db=db, filename=file.filename, explicit_table_name=table_name)
