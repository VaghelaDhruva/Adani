import pandas as pd
from typing import List, Dict, Any
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.utils.exceptions import DataValidationError


async def ingest_csv(file: UploadFile, table_name: str, db: Session) -> Dict[str, Any]:
    """
    Generic CSV ingestion stub.
    Later: map columns to Pydantic schemas, validate, and bulk-insert.
    """
    if not file.filename.endswith(".csv"):
        raise DataValidationError("Only CSV files are supported")

    try:
        contents = await file.read()
        df = pd.read_csv(pd.io.common.StringIO(contents.decode("utf-8")))
    except Exception as e:
        raise DataValidationError(f"Failed to read CSV: {e}")

    # Placeholder: basic shape check
    if df.empty:
        raise DataValidationError("CSV is empty")

    # TODO: map columns, validate with Pydantic, and bulk-insert via SQLAlchemy
    return {"filename": file.filename, "rows_loaded": len(df), "table": table_name}
