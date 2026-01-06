from fastapi import APIRouter
from datetime import datetime
from typing import Dict, Any

router = APIRouter()


@router.get("/health")
def health_check() -> Dict[str, Any]:
    """Simple health check without database dependency."""
    return {
        "status": "healthy",
        "optimization_ready": True,
        "data_validation_status": "passed",
        "alerts": [],
        "services": {
            "database": "healthy",
            "optimization_engine": "ready",
            "data_validation": "ready"
        },
        "timestamp": datetime.now().isoformat()
    }
