from celery import Celery
from typing import Any, Dict, List
import logging
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.api.v1.routes_scenarios import _load_optimization_data
from app.services.audit_service import audit_timer
from app.services.scenarios.scenario_generator import ScenarioConfig
from app.services.scenarios.scenario_runner import run_batch_scenarios_from_configs


settings = get_settings()

# Initialize Celery app
celery_app = Celery(
    "clinker_opt",
<<<<<<< HEAD
    broker=settings.BROKER_URL,
    backend=settings.RESULT_BACKEND,
=======
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
>>>>>>> d4196135 (Fixed Bug)
    include=["app.services.job_queue"],
)

logger = logging.getLogger(__name__)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(bind=True, name="run_scenarios_task")
def run_scenarios_task(self, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Celery task to execute one or more optimization scenarios.

    The input is a list of plain dicts that conform to ScenarioConfig; the
    task reconstructs the Pydantic models, loads optimization data from the
    database, and delegates execution to the existing scenario runner.
    """
    # Import inside task to avoid circular imports at worker startup.
    from app.utils.exceptions import DataValidationError, OptimizationError

    self.update_state(state="STARTED", meta={"status": "running"})

    db = SessionLocal()
    user = "celery-worker"
    metadata = {
        "task_id": self.request.id,
        "scenario_count": len(scenarios),
        "scenario_names": [cfg.get("name") for cfg in scenarios if cfg.get("name")],
    }

    try:
        with audit_timer(user, "run_scenarios_task", db, metadata) as timer:
            data = _load_optimization_data(db)
            if data["demand_forecast"].empty:
                raise DataValidationError("No demand data available for scenarios")

            configs = [ScenarioConfig(**cfg) for cfg in scenarios]
            result = run_batch_scenarios_from_configs(data, configs)
            timer.set_success()
            return result
    except (DataValidationError, OptimizationError) as e:
        # Let Celery mark the task as FAILURE while keeping the error message simple.
        logger.error("Celery task failed", extra={"task_id": self.request.id, "error": str(e)})
        raise Exception(str(e))
    except Exception:
        # Re-raise unexpected errors; traceback is kept in Celery backend but
        # the API layer will not expose it.
        logger.error("Unexpected error in Celery task", extra={"task_id": self.request.id})
        raise
    finally:
        db.close()
