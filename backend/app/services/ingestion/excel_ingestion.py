import pandas as pd
from typing import Dict, Any
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.utils.exceptions import DataValidationError


async def ingest_excel(file: UploadFile, table_name: str, db: Session) -> Dict[str, Any]:
    """
    Generic Excel ingestion stub.
    Later: detect sheets, map columns, validate, and bulk-insert.
    """
    if not (file.filename.endswith(".xlsx") or file.filename.endswith(".xls")):
        raise DataValidationError("Only Excel files (.xlsx/.xls) are supported")

    try:
        contents = await file.read()
        df = pd.read_excel(pd.io.common.BytesIO(contents))
    except Exception as e:
        raise DataValidationError(f"Failed to read Excel: {e}")

    if df.empty:
        raise DataValidationError("Excel file is empty or unreadable")

    # TODO: map columns, validate with Pydantic, and bulk-insert via SQLAlchemy
    return {"filename": file.filename, "rows_loaded": len(df), "table": table_name}
