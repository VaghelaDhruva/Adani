import pdfplumber
import pandas as pd
from typing import List, Dict, Any
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.utils.exceptions import DataValidationError


async def ingest_pdf(file: UploadFile, table_name: str, db: Session) -> Dict[str, Any]:
    """
    Best-effort PDF ingestion using pdfplumber.
    Extract tables and attempt to map to known schemas.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise DataValidationError("Only PDF files are supported")

    try:
        contents = await file.read()
        with pdfplumber.open(pd.io.common.BytesIO(contents)) as pdf:
            tables = []
            for page in pdf.pages:
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)
    except Exception as e:
        raise DataValidationError(f"Failed to read PDF: {e}")

    if not tables:
        raise DataValidationError("No tables found in PDF")

    # For now, return first table as DataFrame placeholder
    df = pd.DataFrame(tables[0][1:], columns=tables[0][0])
    # TODO: smarter schema detection and mapping
    return {"filename": file.filename, "rows_loaded": len(df), "table": table_name}
