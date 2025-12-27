#!/usr/bin/env python3
"""
Company Reports Ingestion Script (placeholder).
Accepts a list of URLs to PDF/HTML reports.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.services.ingestion.industry_data_ingestion import ingest_company_reports
from app.db.base import SessionLocal


async def main(urls):
    db = SessionLocal()
    try:
        results = await ingest_company_reports(urls)
        for r in results:
            print(f"{r['url']}: {r['status']}")
        # TODO: parse and insert structured data into DB
    finally:
        db.close()


if __name__ == "__main__":
    # Example usage: python scripts/ingest_company_reports.py https://example.com/report.pdf
    urls = sys.argv[1:] if len(sys.argv) > 1 else []
    if not urls:
        print("Provide one or more report URLs as arguments.")
        sys.exit(1)
    asyncio.run(main(urls))
